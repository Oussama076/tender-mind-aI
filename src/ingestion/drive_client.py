import os
import io
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# Scopes for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
# Read exclusively from environment, no hardcoded fallbacks
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

logger = logging.getLogger(__name__)

def get_drive_service():
    """Authenticates and returns the Google Drive API service."""
    creds = None
    if SERVICE_ACCOUNT_FILE and os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    else:
        logger.error("CRITICAL: Service account file not configured or not found. Check GOOGLE_APPLICATION_CREDENTIALS.")
        return None
    
    return build('drive', 'v3', credentials=creds)

def download_rfp_from_drive(file_id: str, destination_folder: str = "data/raw"):
    """Downloads a file from Google Drive to the local data/raw folder."""
    service = get_drive_service()
    if not service:
        raise Exception("Could not initialize Google Drive Service.")
        
    try:
        # Get file metadata to retrieve the filename
        file_metadata = service.files().get(fileId=file_id).execute()
        # Sanitize file name to prevent directory traversal
        raw_name = file_metadata.get('name', f"rfp_{file_id}.pdf")
        file_name = os.path.basename(raw_name)
        
        os.makedirs(destination_folder, exist_ok=True)
        # Ensure destination path is strictly within the destination_folder
        destination_path = os.path.abspath(os.path.join(destination_folder, file_name))
        if not destination_path.startswith(os.path.abspath(destination_folder)):
            raise ValueError("Path traversal attempt detected in filename.")
        
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(destination_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        logger.info(f"Downloading {file_name}...")
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                logger.info(f"Download {int(status.progress() * 100)}%.")
            
        logger.info(f"File downloaded successfully to {destination_path}")
        return destination_path
    except Exception as e:
        logger.error(f"Failed to download file {file_id} from Google Drive: {e}")
        raise

def list_files_in_folder(folder_id: str):
    """Lists files in a specific Google Drive folder."""
    service = get_drive_service()
    if not service:
        return []
    
    query = f"'{folder_id}' in parents and trashed=false"
    try:
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        return results.get('files', [])
    except Exception as e:
        logger.error(f"Failed to list files in folder {folder_id}: {e}")
        raise

def list_rfp_files():
    """Returns a list of all RFP files in the configured Drive folder."""
    folder_id = os.getenv("DRIVE_RFP_FOLDER_ID")
    if not folder_id:
        logger.warning("DRIVE_RFP_FOLDER_ID not set. Cannot list RFP files.")
        return []
    
    files = list_files_in_folder(folder_id)
    return [{"name": f.get("name"), "id": f.get("id")} for f in files]
