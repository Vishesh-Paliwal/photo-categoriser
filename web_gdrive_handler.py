"""
Web-based Google Drive handler using gdown for individual files.
"""

import os
import gdown
import re
import requests
from bs4 import BeautifulSoup


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}


class WebGDriveHandler:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.downloaded_count = 0
        self.session = requests.Session()
    
    def _is_image(self, filename):
        """Check if file is an image."""
        return any(filename.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
    
    def _get_folder_file_ids(self, folder_id):
        """Extract file IDs from public folder using web scraping."""
        try:
            url = f"https://drive.google.com/drive/folders/{folder_id}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"Failed to access folder: {response.status_code}")
                return []
            
            # Parse the page to find file IDs
            content = response.text
            
            # Extract file data from the page's JavaScript
            # Look for file entries in the page data
            file_data = []
            
            # Pattern to find file IDs and names
            # Google Drive embeds data in a specific format
            pattern = r'\["([a-zA-Z0-9_-]{25,})",[^\]]*?"([^"]+\.(?:jpg|jpeg|png|gif|bmp|webp))"'
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            seen = set()
            for file_id, filename in matches:
                if file_id not in seen and len(file_id) > 20:
                    file_data.append({'id': file_id, 'name': filename})
                    seen.add(file_id)
            
            # Also try alternative pattern
            if not file_data:
                pattern2 = r'"([a-zA-Z0-9_-]{28,})"[^}]*?"name":"([^"]+\.(?:jpg|jpeg|png|gif|bmp|webp))"'
                matches2 = re.findall(pattern2, content, re.IGNORECASE)
                for file_id, filename in matches2:
                    if file_id not in seen:
                        file_data.append({'id': file_id, 'name': filename})
                        seen.add(file_id)
            
            print(f"Found {len(file_data)} image files in folder")
            return file_data
            
        except Exception as e:
            print(f"Error getting folder contents: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _download_file_gdown(self, file_id, file_path):
        """Download a single file using gdown."""
        try:
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, file_path, quiet=True)
            
            # Check if file was actually downloaded
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return True
            return False
            
        except Exception as e:
            print(f"Error downloading {file_id}: {e}")
            return False
    
    def download_folder(self, folder_id, output_dir):
        """Download all photos from public folder."""
        os.makedirs(output_dir, exist_ok=True)
        photo_paths = []
        self.downloaded_count = 0
        
        print(f"Fetching file list from folder: {folder_id}")
        
        # Get list of files
        files = self._get_folder_file_ids(folder_id)
        
        if not files:
            print("No files found or unable to parse folder")
            return []
        
        total_files = len(files)
        print(f"Starting download of {total_files} files...")
        
        # Download each file
        for idx, file_info in enumerate(files):
            file_path = os.path.join(output_dir, file_info['name'])
            
            print(f"Downloading {idx+1}/{total_files}: {file_info['name']}")
            
            if self._download_file_gdown(file_info['id'], file_path):
                photo_paths.append(file_path)
                self.downloaded_count += 1
                
                # Emit progress
                if self.socketio:
                    self.socketio.emit('progress', {
                        'current_step': f'Downloaded {self.downloaded_count}/{total_files} photos...',
                        'progress': self.downloaded_count,
                        'total': total_files
                    })
            else:
                print(f"Failed to download: {file_info['name']}")
        
        print(f"Successfully downloaded {len(photo_paths)} photos")
        return photo_paths
