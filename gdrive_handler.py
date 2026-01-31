"""
Google Drive handler for downloading photos from folders.
"""

import os
import io
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}


class GDriveHandler:
    def __init__(self, api_key=None):
        """
        Initialize handler. Uses API key for public folders.
        
        Args:
            api_key: Google API key (optional, will try without auth first)
        """
        self.api_key = api_key
        self.service = build('drive', 'v3', developerKey=api_key) if api_key else build('drive', 'v3')
    
    def _is_image(self, filename):
        """Check if file is an image."""
        return any(filename.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
    
    def _list_files(self, folder_id):
        """List all files in a folder (works with public folders)."""
        query = f"'{folder_id}' in parents and trashed=false"
        try:
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, webContentLink)",
                supportsAllDrives=True
            ).execute()
            return results.get('files', [])
        except Exception as e:
            print(f"Error listing files: {e}")
            return []

    def _download_file(self, file_id, file_path):
        """Download a single file (works with public files)."""
        try:
            # Try direct download for public files
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
            response = requests.get(url, stream=True)
            
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            
            # Fallback to API method
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            with open(file_path, 'wb') as f:
                f.write(fh.getvalue())
            return True
            
        except Exception as e:
            print(f"    Error downloading file: {e}")
            return False
    
    def download_folder(self, folder_id, output_dir):
        """Recursively download all photos from folder and subfolders."""
        os.makedirs(output_dir, exist_ok=True)
        photo_paths = []
        
        def process_folder(fid, path):
            files = self._list_files(fid)
            
            for file in files:
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursively process subfolder
                    subfolder_path = os.path.join(path, file['name'])
                    os.makedirs(subfolder_path, exist_ok=True)
                    process_folder(file['id'], subfolder_path)
                elif self._is_image(file['name']):
                    # Download image
                    file_path = os.path.join(path, file['name'])
                    print(f"  Downloading: {file['name']}")
                    self._download_file(file['id'], file_path)
                    photo_paths.append(file_path)
        
        process_folder(folder_id, output_dir)
        return photo_paths
