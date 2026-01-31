#!/usr/bin/env python3
"""
Test script for Haldi photos with web gallery for verification.
Run this to process Haldi photos and launch a browser gallery.
"""

import os
import sys
import webbrowser
import warnings
warnings.filterwarnings('ignore')

from flask import Flask, render_template_string, send_from_directory
from improved_face_processor import ImprovedFaceProcessor

# Configuration
SOURCE_DIR = "photos_source/01 Haldi"
OUTPUT_DIR = "test_output/haldi_organized"

app = Flask(__name__)

GALLERY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Haldi Photos - Face Verification</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .header {
            background: rgba(0,0,0,0.3);
            padding: 20px 40px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 {
            font-size: 2rem;
            background: linear-gradient(90deg, #f39c12, #e74c3c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stats {
            margin-top: 10px;
            color: #aaa;
        }
        .container { padding: 30px; }
        .person-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
        }
        .person-card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .person-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }
        .person-header {
            display: flex;
            align-items: center;
            padding: 15px;
            background: rgba(0,0,0,0.2);
            gap: 15px;
        }
        .avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #f39c12;
        }
        .person-info h3 {
            font-size: 1.2rem;
            color: #f39c12;
        }
        .person-info p {
            color: #888;
            font-size: 0.9rem;
        }
        .photo-scroll {
            display: flex;
            gap: 10px;
            padding: 15px;
            overflow-x: auto;
            background: rgba(0,0,0,0.1);
        }
        .photo-scroll::-webkit-scrollbar {
            height: 8px;
        }
        .photo-scroll::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.2);
        }
        .photo-scroll::-webkit-scrollbar-thumb {
            background: #f39c12;
            border-radius: 4px;
        }
        .photo-thumb {
            width: 100px;
            height: 100px;
            object-fit: cover;
            border-radius: 8px;
            flex-shrink: 0;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .photo-thumb:hover {
            transform: scale(1.1);
        }
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.95);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal.active { display: flex; }
        .modal img {
            max-width: 90vw;
            max-height: 90vh;
            border-radius: 8px;
        }
        .modal-close {
            position: absolute;
            top: 20px; right: 30px;
            font-size: 40px;
            color: #fff;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌼 Haldi Photos - Face Verification</h1>
        <p class="stats">{{ total_persons }} persons • {{ total_photos }} photos</p>
    </div>
    
    <div class="container">
        <div class="person-grid">
            {% for person in persons %}
            <div class="person-card">
                <div class="person-header">
                    {% if person.avatar %}
                    <img class="avatar" src="/photo/{{ person.id }}/_avatar.jpg" alt="{{ person.id }}">
                    {% else %}
                    <div class="avatar" style="background:#333; display:flex; align-items:center; justify-content:center;">?</div>
                    {% endif %}
                    <div class="person-info">
                        <h3>{{ person.id }}</h3>
                        <p>{{ person.count }} photos</p>
                    </div>
                </div>
                <div class="photo-scroll">
                    {% for photo in person.photos[:20] %}
                    <img class="photo-thumb" src="/photo/{{ person.id }}/{{ photo }}" onclick="showModal(this.src)" alt="">
                    {% endfor %}
                    {% if person.count > 20 %}
                    <div style="display:flex;align-items:center;padding:0 20px;color:#888;">+{{ person.count - 20 }} more</div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <div class="modal" id="modal" onclick="this.classList.remove('active')">
        <span class="modal-close">&times;</span>
        <img id="modal-img" src="" alt="">
    </div>
    
    <script>
        function showModal(src) {
            document.getElementById('modal-img').src = src;
            document.getElementById('modal').classList.add('active');
        }
    </script>
</body>
</html>
"""

def collect_photos(source_dir):
    """Collect all photos from directory."""
    photo_paths = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                photo_paths.append(os.path.join(root, file))
    return photo_paths

def process_haldi():
    """Process Haldi photos with improved algorithm."""
    print("=" * 60)
    print("Processing Haldi Photos with Improved Face Recognition")
    print("=" * 60)
    
    # Collect photos
    print(f"\n[1/2] Collecting photos from {SOURCE_DIR}...")
    photo_paths = collect_photos(SOURCE_DIR)
    print(f"  Found {len(photo_paths)} photos")
    
    if not photo_paths:
        print("No photos found!")
        sys.exit(1)
    
    # Process with improved algorithm
    print(f"\n[2/2] Processing faces...")
    processor = ImprovedFaceProcessor(
        distance_threshold=0.45,  # HAC threshold
        merge_threshold=0.4       # Post-merge threshold
    )
    
    face_groups = processor.process_photos(photo_paths)
    
    # Organize
    print(f"\nOrganizing photos to {OUTPUT_DIR}...")
    processor.organize_photos(face_groups, OUTPUT_DIR)
    
    print("\n" + "=" * 60)
    print("✓ Processing complete!")
    for person_id, photos in sorted(face_groups.items()):
        print(f"  {person_id}: {len(photos)} photos")
    print("=" * 60)
    
    return face_groups

@app.route('/')
def gallery():
    """Serve gallery page."""
    persons = []
    total_photos = 0
    
    if os.path.exists(OUTPUT_DIR):
        for person_id in sorted(os.listdir(OUTPUT_DIR)):
            person_dir = os.path.join(OUTPUT_DIR, person_id)
            if os.path.isdir(person_dir):
                photos = [f for f in os.listdir(person_dir) if not f.startswith('_') and f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                has_avatar = os.path.exists(os.path.join(person_dir, '_avatar.jpg'))
                
                persons.append({
                    'id': person_id,
                    'photos': photos,
                    'count': len(photos),
                    'avatar': has_avatar
                })
                total_photos += len(photos)
    
    # Sort by photo count (descending)
    persons.sort(key=lambda x: x['count'], reverse=True)
    
    return render_template_string(GALLERY_HTML, 
                                  persons=persons, 
                                  total_persons=len(persons),
                                  total_photos=total_photos)

@app.route('/photo/<person>/<filename>')
def serve_photo(person, filename):
    """Serve organized photos."""
    return send_from_directory(OUTPUT_DIR, f"{person}/{filename}")

if __name__ == "__main__":
    # Process photos first
    process_haldi()
    
    # Launch web gallery
    print("\n" + "=" * 60)
    print("🌐 Starting verification gallery at http://localhost:5050")
    print("   Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    webbrowser.open('http://localhost:5050')
    app.run(host='0.0.0.0', port=5050, debug=False)
