"""
Simple gallery app to view pre-processed photos.
No processing - just serves the organized photos.
"""

from flask import Flask, render_template, jsonify, send_file
import os
import json

app = Flask(__name__)

PHOTOS_DIR = 'static/organized_photos'


@app.route('/')
def index():
    return render_template('gallery.html')


@app.route('/api/gallery')
def get_gallery():
    """Get all organized photos data with person face avatars."""
    if not os.path.exists(PHOTOS_DIR):
        return jsonify({'error': 'Photos not processed yet'}), 404
    
    gallery = {}
    
    for person_folder in sorted(os.listdir(PHOTOS_DIR)):
        person_path = os.path.join(PHOTOS_DIR, person_folder)
        
        if os.path.isdir(person_path):
            photos = []
            avatar = None
            
            # Check for face crop avatar first
            avatar_path = os.path.join(person_path, '_avatar.jpg')
            if os.path.exists(avatar_path):
                avatar = f'/static/organized_photos/{person_folder}/_avatar.jpg'
            
            for photo in sorted(os.listdir(person_path)):
                if photo == '_avatar.jpg':
                    continue  # Skip avatar file in photo list
                    
                if photo.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                    photo_url = f'/static/organized_photos/{person_folder}/{photo}'
                    photos.append({
                        'filename': photo,
                        'url': photo_url
                    })
                    
                    # Fallback to first photo if no avatar
                    if not avatar:
                        avatar = photo_url
            
            if photos:
                gallery[person_folder] = {
                    'count': len(photos),
                    'photos': photos,
                    'avatar': avatar
                }
    
    return jsonify(gallery)


@app.route('/api/download/person/<person>')
def download_person(person):
    """Download all photos for a person as zip."""
    import zipfile
    import tempfile
    
    person_dir = os.path.join(PHOTOS_DIR, person)
    
    if not os.path.exists(person_dir):
        return jsonify({'error': 'Person not found'}), 404
    
    # Create temp zip file
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for photo in os.listdir(person_dir):
            photo_path = os.path.join(person_dir, photo)
            if os.path.isfile(photo_path):
                zipf.write(photo_path, photo)
    
    return send_file(temp_zip.name, as_attachment=True, download_name=f'{person}_photos.zip')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
