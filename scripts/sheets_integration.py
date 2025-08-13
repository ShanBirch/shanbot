from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import os


class GoogleSheetsManager:
    def __init__(self, service_account_email=None):
        """Initialize the Google Sheets manager with service account credentials."""
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        self.SPREADSHEET_ID = '1nDVn6jhkYBubVTQqbYU3PKo_WooeuTsQzsaNNcQdJlo'  # Your sheet ID
        self.RANGE_NAME = 'Sheet1!A:B'  # Your sheet name and range

        try:
            # Load credentials from the JSON file
            credentials_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\sheets_credentials.json"

            # --- Added Debugging ---
            print(
                f"DEBUG [Sheets Init]: Attempting to load credentials from: {credentials_path}")
            if not os.path.exists(credentials_path):
                print(
                    f"DEBUG [Sheets Init]: ERROR - Path does NOT exist: {credentials_path}")
            elif not os.path.isfile(credentials_path):
                print(
                    f"DEBUG [Sheets Init]: ERROR - Path is NOT a file: {credentials_path}")
            else:
                print(
                    f"DEBUG [Sheets Init]: OK - Path exists and is a file: {credentials_path}")
                try:
                    with open(credentials_path, 'r') as f_test:
                        content_start = f_test.read(
                            100)  # Read first 100 chars
                        print(
                            f"DEBUG [Sheets Init]: OK - Successfully opened and read start of file: {content_start}...")
                except Exception as read_err:
                    print(
                        f"DEBUG [Sheets Init]: ERROR - Failed to open/read file: {read_err}")
            # --- End of Debugging ---

            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=self.SCOPES
            )

            # Build the Sheets API service
            self.service = build('sheets', 'v4', credentials=credentials)
            print("✅ Google Sheets API initialized successfully")

        except Exception as e:
            print(f"❌ Error initializing Google Sheets: {e}")
            raise

    def find_username_row(self, username):
        """Find the row number of a username in column A."""
        try:
            # --- Diagnostic Step: Try getting sheet properties first ---
            print(
                f"DEBUG [Sheets Find]: Attempting to get properties for SPREADSHEET_ID: {self.SPREADSHEET_ID}")
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.SPREADSHEET_ID).execute()
            sheets = sheet_metadata.get('sheets', '')
            sheet_names = [s.get("properties", {}).get("title", "")
                           for s in sheets]
            print(
                f"DEBUG [Sheets Find]: Successfully got metadata. Available sheets: {sheet_names}")
            # Check if 'Sheet1' exists in the list of sheet names
            if 'Sheet1' not in sheet_names:
                print(
                    f"DEBUG [Sheets Find]: CRITICAL ERROR - Sheet named 'Sheet1' not found in spreadsheet metadata!")
                return None  # Cannot proceed if sheet doesn't exist
            # --- End Diagnostic Step ---

            # Get all values from column A
            # Added debug
            print(
                f"DEBUG [Sheets Find]: Attempting to read range 'Sheet1!A:A'")
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range='Sheet1!A:A'
            ).execute()

            values = result.get('values', [])

            # Search for username
            # Start from 1 for actual row numbers
            for i, row in enumerate(values, 1):
                if row and row[0].lower() == username.lower():
                    return i

            return None  # Username not found

        except Exception as e:
            print(f"❌ Error finding username row for '{username}': {e}")
            return None

    def find_user(self, username):
        """Find a user by username and return their data.

        Args:
            username: Instagram username to search for

        Returns:
            Dictionary with user data including conversation_topics if available
        """
        try:
            if not username:
                print("❌ Error: Empty username provided to find_user")
                return None

            print(f"🔍 Searching for user: {username}")
            row_number = self.find_username_row(username)

            if not row_number:
                print(f"⚠️ User {username} not found in spreadsheet")
                return None

            # Get value from column B for this row
            range_name = f'Sheet1!B{row_number}'
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.SPREADSHEET_ID,
                range=range_name
            ).execute()

            values = result.get('values', [])
            if not values or not values[0]:
                print(f"⚠️ No data found in column B for {username}")
                return None

            # Parse the JSON data from column B
            json_data = values[0][0]
            try:
                user_data = json.loads(json_data)

                # Log if conversation topics are found
                if "conversation_topics" in user_data:
                    topic_count = len(user_data["conversation_topics"]) if isinstance(
                        user_data["conversation_topics"], list) else 1
                    print(
                        f"✅ Found {topic_count} conversation topics for {username}")

                return user_data

            except json.JSONDecodeError:
                print(
                    f"❌ Error: Column B data for {username} is not valid JSON: {json_data}")
                return {
                    "description": f"Profile for {username}",
                    "message_text": json_data,  # Use raw text as message text
                    "timestamp": ""
                }

        except Exception as e:
            print(f"❌ Error in find_user: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_sheet(self, username, combined_data):
        """Finds username in Col A, updates Col B, or appends a new row."""
        try:
            # Find if username exists
            row_number = self.find_username_row(username)

            if row_number:
                # Update existing row - only column B
                print(
                    f"✅ Found existing row for {username} at row {row_number}. Updating column B.")
                # Target only column B of the specific row
                range_name = f'Sheet1!B{row_number}'
                # Prepare the value for the cell (list of lists)
                values = [[combined_data]]

                body = {
                    'values': values
                }

                # Use update for the specific cell
                result = self.service.spreadsheets().values().update(
                    spreadsheetId=self.SPREADSHEET_ID,
                    range=range_name,
                    valueInputOption='RAW',  # Use RAW to treat data as entered
                    body=body
                ).execute()

                print(
                    f"✅ Updated column B for {username} at row {row_number}.")

            else:
                # Username not found, append a new row
                print(f"ℹ️ Username {username} not found. Appending new row.")
                # Data for the new row [Column A value, Column B value]
                values = [[username, combined_data]]

                body = {
                    'values': values
                }

                # Use append to add the new row after the last row with data in the specified range
                result = self.service.spreadsheets().values().append(
                    spreadsheetId=self.SPREADSHEET_ID,
                    range='Sheet1!A:B',  # Append data starting from column A in the first empty row
                    valueInputOption='RAW',  # Use RAW
                    insertDataOption='INSERT_ROWS',  # Insert as new rows
                    body=body
                ).execute()

                updates = result.get('updates', {})
                updated_range = updates.get('updatedRange', 'N/A')
                print(
                    f"✅ Appended new row for {username}. Updated range: {updated_range}")

            return True  # Indicate success

        except Exception as e:
            print(f"❌ Error updating Google Sheet for {username}: {e}")
            import traceback
            traceback.print_exc()  # Print detailed traceback for debugging
            return False  # Indicate failure

    def add_row(self, row_data):
        """Add or update a row in the Google Sheet using data from the bot.

        Args:
            row_data: Dictionary containing data to be saved, including username and conversation_topics
        """
        try:
            username = row_data.get("username", "")
            if not username:
                print("❌ Error: Username is missing from row_data")
                return False

            # Prepare data for column B - make sure to include conversation_topics
            # This is what the manychat_webhook will read for profile info and conversation topics
            column_b_data = {
                "timestamp": row_data.get("timestamp", ""),
                "description": row_data.get("description", ""),
                "message_text": row_data.get("message_text", ""),
                "message_sent": row_data.get("message_sent", "No"),
            }

            # Add conversation topics if available - this is the key part for our integration
            if "conversation_topics" in row_data and row_data["conversation_topics"]:
                column_b_data["conversation_topics"] = row_data["conversation_topics"]
                print(
                    f"✅ Adding conversation topics to sheet data: {row_data['conversation_topics']}")

            # Convert to JSON string for storage in column B
            combined_data = json.dumps(column_b_data)

            # Use existing update_sheet method to either update or append
            result = self.update_sheet(username, combined_data)

            return result

        except Exception as e:
            print(f"❌ Error in add_row for sheet data: {e}")
            import traceback
            traceback.print_exc()
            return False
