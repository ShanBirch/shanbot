import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import logging
import time


def print_step(message):
    """Print a step with clear formatting"""
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50 + "\n")


def print_substep(message):
    """Print a substep with clear formatting"""
    print("-" * 30)
    print(message)
    print("-" * 30)


class GoogleSheetsManager:
    """Handle interactions with Google Sheets"""

    def __init__(self, service_account_email=None):
        """Initialize the Google Sheets manager with service account credentials."""
        try:
            # Initialize with credentials
            self.scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            self.client = None  # Initialize client as None
            self.spreadsheet = None
            self.worksheet = None
            self.initialized = False
            self.service_account_email = service_account_email  # Store email if provided

            # Define expected headers based on new structure
            self.expected_headers = [
                "Username", "Conversation Opener", "Last Interaction Date", "Status"
            ]

            # Try to load credentials from service account JSON file
            try:
                # Ensure credentials file exists
                if not os.path.exists('sheets_credentials.json'):
                    print("❌ Error: 'sheets_credentials.json' not found.")
                    print(
                        "Please ensure the Google Cloud service account key file is present.")
                    return  # Stop initialization if file missing

                self.credentials = Credentials.from_service_account_file(
                    'sheets_credentials.json',
                    scopes=self.scopes
                )
                self.client = gspread.authorize(self.credentials)

                # Set spreadsheet and worksheet details
                self.spreadsheet_name = "Lead chat"
                self.worksheet_name = "Sheet1"

                # Try to open existing spreadsheet or create a new one
                try:
                    self.spreadsheet = self.client.open(self.spreadsheet_name)
                    print(
                        f"✅ Opened existing spreadsheet: {self.spreadsheet_name}")
                except gspread.exceptions.SpreadsheetNotFound:
                    # Create a new spreadsheet if one doesn't exist
                    print(
                        f"Spreadsheet '{self.spreadsheet_name}' not found, creating...")
                    self.spreadsheet = self.client.create(
                        self.spreadsheet_name)
                    # Share with the service account email if provided, otherwise might need manual sharing
                    if self.service_account_email:
                        try:
                            self.spreadsheet.share(
                                self.service_account_email, perm_type='user', role='writer')
                            print(
                                f"Shared spreadsheet with {self.service_account_email}")
                        except Exception as share_error:
                            print(
                                f"⚠️ Could not automatically share spreadsheet: {share_error}")
                            print("Please share manually if needed.")
                    print(
                        f"✅ Created new spreadsheet: {self.spreadsheet_name}")

                # Check if the worksheet exists or create it
                try:
                    self.worksheet = self.spreadsheet.worksheet(
                        self.worksheet_name)
                    print(f"✅ Using existing worksheet: {self.worksheet_name}")
                    # Optional: Check if headers match and update if necessary
                    # current_headers = self.worksheet.row_values(1)
                    # if current_headers != self.expected_headers:
                    #     print("Headers mismatch, updating...")
                    #     # Handle header update carefully (potential data loss/shift)
                    #     pass
                except gspread.exceptions.WorksheetNotFound:
                    # Create the worksheet with the correct headers
                    print(
                        f"Worksheet '{self.worksheet_name}' not found, creating...")
                    self.worksheet = self.spreadsheet.add_worksheet(
                        # Add buffer col
                        title=self.worksheet_name, rows=1000, cols=len(self.expected_headers) + 1
                    )
                    self.worksheet.append_row(
                        self.expected_headers)  # Use defined headers
                    print(
                        f"✅ Created new worksheet with headers: {self.worksheet_name}")

                print("✅ Google Sheets connection successfully initialized")
                self.initialized = True

            except Exception as e:
                print(f"❌ Error initializing Google Sheets client: {e}")
                self.initialized = False

        except Exception as e:
            print(f"❌ Google Sheets setup error: {e}")
            self.initialized = False

    def update_sheet(self, username, combined_data, status="Completed"):
        """Update the Google Sheet with combined data for a user.

        Args:
            username (str): The Instagram username.
            combined_data (str): The combined string of analysis and DM sent.
            status (str, optional): The status of the interaction. Defaults to "Completed".
        """
        if not self.initialized:
            print("⚠️ Google Sheets manager not properly initialized. Cannot update.")
            return False

        try:
            # Get timestamp
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d %H:%M:%S")

            # Column indices (1-based)
            username_col = 1
            opener_col = 2
            date_col = 3
            status_col = 4

            # Try to find the username
            try:
                cell = self.worksheet.find(username, in_column=username_col)
                if cell:
                    print(
                        f"DEBUG [Sheets Int]: Found {username} at cell {gspread.utils.rowcol_to_a1(cell.row, cell.col)} (Row: {cell.row})")
                else:
                    # This case should be handled by the except block, but logging just in case
                    print(
                        f"DEBUG [Sheets Int]: worksheet.find did not return a cell for {username}.")
            except gspread.exceptions.CellNotFound:
                print(
                    f"DEBUG [Sheets Int]: CellNotFound exception for {username}. Will append new row.")
                cell = None
            except gspread.exceptions.APIError as e:
                # Handle API rate limits during find operation
                if "RESOURCE_EXHAUSTED" in str(e) or (hasattr(e, 'response') and e.response.status_code == 429):
                    print(
                        "⚠️ Google Sheets API rate limit reached during find, waiting 60 seconds...")
                    time.sleep(60)
                    # Retry
                    return self.update_sheet(username, combined_data, status)
                else:
                    print(f"❌ Unexpected API Error during find: {e}")
                    logging.error(f"Google Sheets find API Error: {e}")
                    return False  # Don't proceed if find fails unexpectedly
            except Exception as find_e:
                print(f"❌ Error finding user {username}: {find_e}")
                logging.error(f"Error finding user {username}: {find_e}")
                return False  # Don't proceed if find fails

            # Prepare updates
            updates = [
                {'range': gspread.utils.rowcol_to_a1(cell.row, opener_col) if cell else None,
                 'values': [[combined_data]]},
                {'range': gspread.utils.rowcol_to_a1(cell.row, date_col) if cell else None,
                 'values': [[date_str]]},
                {'range': gspread.utils.rowcol_to_a1(cell.row, status_col) if cell else None,
                 'values': [[status]]}
            ]

            if cell:
                # Username exists, update the existing row using batch update
                # Use the previously logged row number from the DEBUG message
                print(
                    f"DEBUG [Sheets Int]: Preparing batch update for row {cell.row}...")
                update_payload = [u for u in updates if u['range'] is not None]
                if update_payload:
                    print(
                        f"DEBUG [Sheets Int]: Batch update payload: {update_payload}")
                    try:
                        response = self.worksheet.batch_update(
                            update_payload, value_input_option='USER_ENTERED')
                        print(
                            f"DEBUG [Sheets Int]: batch_update response for {username}: {response}")
                        print(
                            f"✅ Successfully called batch_update for {username} at row {cell.row}")
                        return True
                    except Exception as batch_e:
                        print(
                            f"❌ DEBUG [Sheets Int]: Error during batch_update for {username}: {batch_e}")
                        logging.error(
                            f"Error during batch_update for {username}: {batch_e}")
                        return False
                else:
                    # Should not happen
                    print(f"⚠️ No updates to perform for {username}?")
                    return False
            else:
                # Username doesn't exist, add a new row
                print(
                    f"DEBUG [Sheets Int]: Preparing to append new row for {username}...")
                row_data = [username, combined_data, date_str, status]
                print(f"DEBUG [Sheets Int]: Row data to append: {row_data}")
                try:
                    response = self.worksheet.append_row(
                        row_data, value_input_option='USER_ENTERED')
                    print(
                        f"DEBUG [Sheets Int]: append_row response for {username}: {response}")
                    print(f"✅ Successfully called append_row for {username}")
                    return True
                except Exception as append_e:
                    print(
                        f"❌ DEBUG [Sheets Int]: Error during append_row for {username}: {append_e}")
                    logging.error(
                        f"Error during append_row for {username}: {append_e}")
                    return False

        except gspread.exceptions.APIError as e:
            # Handle API rate limits during update/append
            if "RESOURCE_EXHAUSTED" in str(e) or (hasattr(e, 'response') and e.response.status_code == 429):
                print(
                    "⚠️ Google Sheets API rate limit reached during update/append, waiting 60 seconds...")
                time.sleep(60)
                # Retry the operation
                return self.update_sheet(username, combined_data, status)
            else:
                print(f"❌ Google Sheets API Error during update/append: {e}")
                logging.error(f"Google Sheets update/append API Error: {e}")
                return False
        except Exception as e:
            print(
                f"❌ Error updating/appending Google Sheet for {username}: {e}")
            logging.error(
                f"Error updating/appending Google Sheet for {username}: {e}")
            return False

    def get_last_analysis(self, username):
        """Retrieves the 'Post Analysis' part from the 'Conversation Opener' column.

        Args:
            username (str): The Instagram username.

        Returns:
            dict: A dictionary like {"description": "..."} if found, otherwise None.
        """
        if not self.initialized:
            print(
                "⚠️ Google Sheets manager not properly initialized. Cannot get analysis.")
            return None

        try:
            # Column indices (1-based)
            username_col = 1
            opener_col = 2

            cell = self.worksheet.find(username, in_column=username_col)
            if cell:
                # Get the combined data from the 'Conversation Opener' column
                combined_data = self.worksheet.cell(cell.row, opener_col).value
                if combined_data and isinstance(combined_data, str):
                    # Try to parse the description
                    # Assumes format "Post Analysis: [DESCRIPTION]\n\nDM Sent: [DM]"
                    lines = combined_data.split('\n')
                    if lines and lines[0].startswith("Post Analysis:"):
                        description = lines[0].replace(
                            "Post Analysis:", "").strip()
                        return {"description": description}
                    else:
                        print(
                            f"⚠️ Could not parse description from column B for {username}")
                        return None
                else:
                    return None  # No data in cell
            else:
                return None  # User not found

        except gspread.exceptions.CellNotFound:
            return None  # User not found
        except gspread.exceptions.APIError as e:
            if "RESOURCE_EXHAUSTED" in str(e) or (hasattr(e, 'response') and e.response.status_code == 429):
                print(
                    "⚠️ Google Sheets API rate limit reached during get_last_analysis, waiting 60s...")
                time.sleep(60)
                return self.get_last_analysis(username)  # Retry
            else:
                print(f"❌ API Error getting analysis for {username}: {e}")
                logging.error(
                    f"API Error getting analysis for {username}: {e}")
                return None
        except Exception as e:
            print(f"❌ Error getting analysis for {username}: {e}")
            logging.error(f"Error getting analysis for {username}: {e}")
            return None
