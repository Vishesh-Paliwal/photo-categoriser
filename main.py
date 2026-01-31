#!/usr/bin/env python3
"""
Photo Face Recognition App
Downloads photos from Google Drive and organizes them by detected faces.
"""

import os
import sys
from gdrive_handler import GDriveHandler
from face_processor import FaceProcessor


def extract_folder_id(url):
    """Extract folder ID from Google Drive URL."""
    if '/folders/' in url:
        return url.split('/folders/')[-1].split('?')[0]
    return url


def main():
    print("=" * 60)
    print("Photo Face Recognition App")
    print("=" * 60)
    
    # Get Google Drive folder link
    gdrive_url = input("\nEnter Google Drive folder link: ").strip()
    folder_id = extract_folder_id(gdrive_url)
    
    if not folder_id:
        print("Error: Invalid Google Drive URL")
        sys.exit(1)
    
    # Initialize handlers
    print("\n[1/4] Connecting to Google Drive...")
    api_key = os.environ.get('GOOGLE_API_KEY')  # Optional: set API key for better rate limits
    gdrive = GDriveHandler(api_key=api_key)
    
    # Download photos
    print("\n[2/4] Downloading photos from Drive...")
    download_dir = "downloads"
    photo_paths = gdrive.download_folder(folder_id, download_dir)
    print(f"Downloaded {len(photo_paths)} photos")
    
    if not photo_paths:
        print("No photos found in the folder")
        sys.exit(0)
    
    # Process faces
    print("\n[3/4] Detecting and recognizing faces...")
    processor = FaceProcessor()
    face_groups = processor.process_photos(photo_paths)
    
    # Organize photos
    print("\n[4/4] Organizing photos by person...")
    output_dir = "output"
    processor.organize_photos(face_groups, output_dir)
    
    print("\n" + "=" * 60)
    print(f"✓ Complete! Photos organized in '{output_dir}/' directory")
    print(f"  - Found {len(face_groups)} unique persons")
    print("=" * 60)


if __name__ == "__main__":
    main()
