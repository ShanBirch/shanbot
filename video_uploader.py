#!/usr/bin/env python
import os
import sys
import argparse
import glob
from datetime import datetime
from pathlib import Path
import json
import time

# You'll need to install these libraries:
# pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Google Drive API scope
SCOPES = ['https://www.googleapis.com/auth/drive']


def authenticate_google_drive():
    """Authenticate with Google Drive API"""
    creds = None

    # The token.json file stores user access tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_info(
            json.loads(open('token.json').read()), SCOPES)

    # If no valid credentials found, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if credentials.json exists
            if not os.path.exists('credentials.json'):
                print("Error: credentials.json file not found!")
                print("Please download OAuth 2.0 credentials from Google Cloud Console")
                print(
                    "and save as 'credentials.json' in the same directory as this script.")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def find_or_create_folder(service, folder_name, parent_id=None):
    """Find or create a folder in Google Drive"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    query += " and trashed=false"

    response = service.files().list(q=query,
                                    spaces='drive',
                                    fields='files(id, name)').execute()

    files = response.get('files', [])

    # If folder exists, return its ID
    if files:
        return files[0]['id']

    # If folder doesn't exist, create it
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    if parent_id:
        folder_metadata['parents'] = [parent_id]

    folder = service.files().create(body=folder_metadata,
                                    fields='id').execute()

    return folder.get('id')


def upload_file(service, file_path, folder_id=None):
    """Upload a file to Google Drive and make it shareable"""
    file_name = os.path.basename(file_path)

    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaFileUpload(file_path, resumable=True)

    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id, webViewLink').execute()

    # Make the file accessible via link (anyone with link can view)
    permission = {
        'type': 'anyone',
        'role': 'reader',
        'allowFileDiscovery': False
    }

    service.permissions().create(
        fileId=file.get('id'),
        body=permission
    ).execute()

    # Refresh to get the updated link
    file = service.files().get(
        fileId=file.get('id'),
        fields='webViewLink'
    ).execute()

    return file.get('webViewLink')


def group_videos_by_date(video_dir):
    """Group videos in the specified directory by date"""
    videos_by_date = {}

    # Find all mp4 files
    video_files = glob.glob(os.path.join(video_dir, "*.mp4"))

    for video_file in video_files:
        # Get file's modification time
        mod_time = os.path.getmtime(video_file)
        date_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')

        if date_str not in videos_by_date:
            videos_by_date[date_str] = []

        videos_by_date[date_str].append(video_file)

    return videos_by_date


def main():
    parser = argparse.ArgumentParser(
        description='Upload client videos to Google Drive and generate shareable links')
    parser.add_argument('--video_dir', type=str, default='output',
                        help='Directory containing the video files')
    parser.add_argument('--date', type=str,
                        help='Specific date to process (YYYY-MM-DD)')
    parser.add_argument('--main_folder', type=str, default='Fitness Videos',
                        help='Main folder name in Google Drive')
    args = parser.parse_args()

    video_dir = Path(args.video_dir)

    if not video_dir.exists() or not video_dir.is_dir():
        print(f"Error: Video directory '{video_dir}' not found!")
        return 1

    # Authenticate with Google Drive
    print("Authenticating with Google Drive...")
    try:
        drive_service = authenticate_google_drive()
    except Exception as e:
        print(f"Error authenticating with Google Drive: {e}")
        return 1

    # Group videos by date
    videos_by_date = group_videos_by_date(video_dir)

    if args.date:
        # Filter for specific date if provided
        if args.date in videos_by_date:
            videos_by_date = {args.date: videos_by_date[args.date]}
        else:
            print(f"No videos found for date: {args.date}")
            return 1

    if not videos_by_date:
        print("No videos found to upload!")
        return 1

    # Create or find main folder in Google Drive
    print(
        f"Finding or creating main folder '{args.main_folder}' in Google Drive...")
    main_folder_id = find_or_create_folder(drive_service, args.main_folder)

    # Process each date group
    links_file = open("video_links.txt", "w")
    links_file.write("Video Links for Instagram\n")
    links_file.write("=" * 40 + "\n\n")

    for date, videos in videos_by_date.items():
        print(f"\nProcessing videos for date: {date}")

        # Create date subfolder
        date_folder_id = find_or_create_folder(
            drive_service, date, main_folder_id)

        links_file.write(f"Date: {date}\n")
        links_file.write("-" * 40 + "\n")

        # Upload each video and generate link
        for video_path in videos:
            client_name = os.path.basename(
                video_path).split('_weekly_checkin.mp4')[0]
            print(f"Uploading video for client: {client_name}...")

            try:
                link = upload_file(drive_service, video_path, date_folder_id)
                print(f"✓ Uploaded successfully: {link}")

                links_file.write(f"{client_name}: {link}\n")

            except Exception as e:
                print(f"Error uploading video: {e}")
                links_file.write(
                    f"{client_name}: Error uploading - {str(e)}\n")

        links_file.write("\n")

    links_file.close()

    print(f"\nAll videos processed! Shareable links have been saved to 'video_links.txt'")

    return 0


if __name__ == "__main__":
    sys.exit(main())
