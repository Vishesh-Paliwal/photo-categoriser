"""
Batch processor for all photo folders.
- Processes each event folder separately
- Organizes photos by person
- Generates thumbnails for web gallery
"""

import os
import shutil
import cv2
import time
from PIL import Image
from improved_face_processor import ImprovedFaceProcessor

# Configuration
SOURCE_ROOT = "photos_source"
OUTPUT_ROOT = "gallery"
THUMB_SIZE = (300, 300)

FOLDERS_TO_PROCESS = [
    "01 Haldi",
    "02 Ring",
    "03 Rituals",
    "04 Wedding"
]

def generate_thumbnail(src_path, dest_path):
    """Generate a thumbnail for the image."""
    try:
        with Image.open(src_path) as img:
            img = img.convert('RGB')
            img.thumbnail(THUMB_SIZE)
            img.save(dest_path, "JPEG", quality=80)
    except Exception as e:
        print(f"Error generating thumbnail for {src_path}: {e}")

def process_folder(folder_name):
    """Process a single event folder."""
    source_dir = os.path.join(SOURCE_ROOT, folder_name)
    
    # Normalize output folder name (lowercase, no spaces)
    # e.g., "01 Haldi" -> "haldi"
    clean_name = folder_name.split(' ', 1)[1].lower() if ' ' in folder_name else folder_name.lower()
    output_dir = os.path.join(OUTPUT_ROOT, clean_name)
    
    print("\n" + "=" * 60)
    print(f"PROCESSING: {folder_name} -> {clean_name}")
    print("=" * 60)
    
    if not os.path.exists(source_dir):
        print(f"Source directory not found: {source_dir}")
        return
    
    # 1. Collect photos
    photo_paths = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                photo_paths.append(os.path.join(root, file))
    
    print(f"Found {len(photo_paths)} photos")
    if not photo_paths:
        return

    # 2. Process faces
    # Tweak thresholds based on folder size if needed
    processor = ImprovedFaceProcessor(
        distance_threshold=0.45,
        merge_threshold=0.4
    )
    
    face_groups = processor.process_photos(photo_paths)
    
    # 3. Organize and generate thumbnails
    print(f"\nExample output: {output_dir}")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    print("Organizing photos and generating thumbnails...")
    
    for person_id, photos in face_groups.items():
        person_dir = os.path.join(output_dir, person_id)
        os.makedirs(person_dir, exist_ok=True)
        
        # Save avatar
        if person_id in processor.face_avatars:
            avatar_path = os.path.join(person_dir, '_avatar.jpg')
            cv2.imwrite(avatar_path, processor.face_avatars[person_id])
        
        # Copy photos and make thumbs
        for photo_path in photos:
            filename = os.path.basename(photo_path)
            dest_path = os.path.join(person_dir, filename)
            thumb_path = os.path.join(person_dir, f"thumb_{filename}")
            
            # Handle duplicates
            counter = 1
            base, ext = os.path.splitext(filename)
            while os.path.exists(dest_path):
                filename = f"{base}_{counter}{ext}"
                dest_path = os.path.join(person_dir, filename)
                thumb_path = os.path.join(person_dir, f"thumb_{filename}")
                counter += 1
            
            # Copy full image
            shutil.copy2(photo_path, dest_path)
            
            # Generate thumbnail
            generate_thumbnail(photo_path, thumb_path)
            
    print(f"Completed {folder_name}")

def main():
    start_time = time.time()
    
    # Clean gallery root but keep index/assets if we had them (not yet)
    # actually better to start fresh for the subfolders
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    
    for folder in FOLDERS_TO_PROCESS:
        process_folder(folder)
        
    duration = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"ALL DONE! Total time: {duration/60:.1f} minutes")
    print("=" * 60)

if __name__ == "__main__":
    main()
