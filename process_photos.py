#!/usr/bin/env python3
"""
One-time script to process photos and organize by faces.
Run this once, then deploy the gallery app.
"""

import os
import shutil
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

from web_face_processor import WebFaceProcessor

def collect_all_photos(source_dir):
    """Collect all photos from nested folders."""
    photo_paths = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                photo_paths.append(os.path.join(root, file))
    return photo_paths

def main():
    print("=" * 60)
    print("Processing Wedding Photos")
    print("=" * 60)
    
    source_dir = "photos_source"
    output_dir = "static/organized_photos"
    
    # Collect all photos
    print("\n[1/3] Collecting photos...")
    photo_paths = collect_all_photos(source_dir)
    total = len(photo_paths)
    print(f"Found {total} photos")
    
    # Process faces with progress
    print(f"\n[2/3] Detecting and grouping faces...")
    print(f"Processing {total} photos with DeepFace + clustering...")
    
    # Use DeepFace with clustering (eps=0.3 for tighter grouping)
    processor = WebFaceProcessor(distance_threshold=0.3)
    face_groups = processor.process_photos(photo_paths)
    print(f"\nFound {len(face_groups)} unique persons:")
    for person_id, photos in sorted(face_groups.items()):
        print(f"  {person_id}: {len(photos)} photos")
    
    # Organize photos
    print("\n[3/3] Organizing photos...")
    processor.organize_photos(face_groups, output_dir)
    
    print("\n" + "=" * 60)
    print("✓ Processing complete!")
    print(f"Photos organized in: {output_dir}/")
    print("=" * 60)

if __name__ == "__main__":
    main()
