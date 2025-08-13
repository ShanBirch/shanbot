import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_drive_service():
    """
    Authenticate and create a Google Drive service.

    Returns:
        A Google Drive service object or None if authentication fails.
    """
    creds = None

    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logging.error(f"Authentication failed: {e}")
                logging.info(
                    "Please download credentials.json from Google Cloud Console")
                return None

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        logging.error(f"Failed to build the Drive service: {e}")
        return None


def upload_video_to_drive(video_path, folder_id=None):
    """
    Upload a video to Google Drive.

    Args:
        video_path (str): Path to the video file.
        folder_id (str, optional): ID of the folder to upload to. If None, uploads to root.

    Returns:
        tuple: (success (bool), file_id (str), web_view_link (str))
    """
    service = get_drive_service()
    if not service:
        return False, None, None

    if not os.path.exists(video_path):
        logging.error(f"Video file not found: {video_path}")
        return False, None, None

    file_name = os.path.basename(video_path)

    # File metadata
    file_metadata = {
        'name': file_name,
        'mimeType': 'video/mp4'
    }

    # If folder_id is provided, set the parent folder
    if folder_id:
        file_metadata['parents'] = [folder_id]

    try:
        # Create media file upload
        media = MediaFileUpload(
            video_path,
            mimetype='video/mp4',
            resumable=True
        )

        # Upload the file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        file_id = file.get('id')

        # Set permissions to make the file accessible via link
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }

        service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()

        # Get the web view link
        file = service.files().get(
            fileId=file_id,
            fields='webViewLink'
        ).execute()

        web_view_link = file.get('webViewLink')

        logging.info(f"Successfully uploaded {file_name} to Google Drive")
        logging.info(f"File ID: {file_id}")
        logging.info(f"Web view link: {web_view_link}")

        return True, file_id, web_view_link

    except Exception as e:
        logging.error(f"Error uploading file to Google Drive: {e}")
        return False, None, None


def create_drive_folder(folder_name):
    """
    Create a folder in Google Drive.

    Args:
        folder_name (str): Name of the folder to create.

    Returns:
        str: ID of the created folder or None if creation fails.
    """
    service = get_drive_service()
    if not service:
        return None

    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    try:
        folder = service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()

        folder_id = folder.get('id')
        logging.info(f"Created folder '{folder_name}' with ID: {folder_id}")

        return folder_id

    except Exception as e:
        logging.error(f"Error creating folder in Google Drive: {e}")
        return None


def get_or_create_fitness_wrapped_folder():
    """
    Get or create a 'Fitness Wrapped Videos' folder in Google Drive.

    Returns:
        str: ID of the folder or None if operation fails.
    """
    service = get_drive_service()
    if not service:
        return None

    folder_name = 'Fitness Wrapped Videos'

    try:
        # Search for existing folder
        results = service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()

        items = results.get('files', [])

        if items:
            # Folder exists, return its ID
            folder_id = items[0]['id']
            logging.info(
                f"Found existing folder '{folder_name}' with ID: {folder_id}")
            return folder_id
        else:
            # Create new folder
            return create_drive_folder(folder_name)

    except Exception as e:
        logging.error(f"Error finding/creating folder in Google Drive: {e}")
        return None
