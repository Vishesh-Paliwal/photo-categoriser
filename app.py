"""
Flask web application for photo face recognition.
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import os
import shutil
import zipfile
from threading import Thread
from web_gdrive_handler import WebGDriveHandler
from web_face_processor import WebFaceProcessor


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
processing_state = {
    'is_processing': False,
    'current_step': '',
    'progress': 0,
    'total': 0,
    'status': 'idle'
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/process', methods=['POST'])
def process_photos():
    """Start processing photos from Google Drive link."""
    global processing_state
    
    if processing_state['is_processing']:
        return jsonify({'error': 'Already processing'}), 400
    
    data = request.json
    gdrive_url = data.get('url', '').strip()
    
    if not gdrive_url:
        return jsonify({'error': 'No URL provided'}), 400
    
    # Extract folder ID
    folder_id = extract_folder_id(gdrive_url)
    if not folder_id:
        return jsonify({'error': 'Invalid Google Drive URL'}), 400
    
    # Start processing in background
    thread = Thread(target=process_in_background, args=(folder_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Processing started', 'folder_id': folder_id})


@app.route('/api/status')
def get_status():
    """Get current processing status."""
    return jsonify(processing_state)


@app.route('/api/results')
def get_results():
    """Get organized photos data for gallery view."""
    output_dir = 'output'
    
    if not os.path.exists(output_dir):
        return jsonify({'error': 'No results available'}), 404
    
    results = {}
    
    for person_folder in os.listdir(output_dir):
        person_path = os.path.join(output_dir, person_folder)
        
        if os.path.isdir(person_path):
            photos = []
            for photo in os.listdir(person_path):
                if photo.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                    photos.append({
                        'filename': photo,
                        'url': f'/api/photo/{person_folder}/{photo}'
                    })
            
            results[person_folder] = {
                'count': len(photos),
                'photos': photos
            }
    
    return jsonify(results)


@app.route('/api/photo/<person>/<filename>')
def get_photo(person, filename):
    """Serve individual photo."""
    photo_path = os.path.join('output', person, filename)
    
    if not os.path.exists(photo_path):
        return jsonify({'error': 'Photo not found'}), 404
    
    return send_file(photo_path, mimetype='image/jpeg')


@app.route('/api/download/person/<person>')
def download_person(person):
    """Download all photos for a specific person as zip."""
    person_dir = os.path.join('output', person)
    
    if not os.path.exists(person_dir):
        return jsonify({'error': 'Person folder not found'}), 404
    
    zip_path = f'{person}_photos.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for photo in os.listdir(person_dir):
            photo_path = os.path.join(person_dir, photo)
            if os.path.isfile(photo_path):
                zipf.write(photo_path, photo)
    
    return send_file(zip_path, as_attachment=True, download_name=f'{person}_photos.zip')


@app.route('/api/download/photo/<person>/<filename>')
def download_single_photo(person, filename):
    """Download a single photo."""
    photo_path = os.path.join('output', person, filename)
    
    if not os.path.exists(photo_path):
        return jsonify({'error': 'Photo not found'}), 404
    
    return send_file(photo_path, as_attachment=True, download_name=filename)


@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """Clean up downloaded and processed files."""
    try:
        if os.path.exists('downloads'):
            shutil.rmtree('downloads')
        if os.path.exists('output'):
            shutil.rmtree('output')
        
        # Clean up any zip files
        for file in os.listdir('.'):
            if file.endswith('_photos.zip'):
                os.remove(file)
        
        global processing_state
        processing_state = {
            'is_processing': False,
            'current_step': '',
            'progress': 0,
            'total': 0,
            'status': 'idle'
        }
        
        return jsonify({'message': 'Cleanup complete'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def extract_folder_id(url):
    """Extract folder ID from Google Drive URL."""
    if '/folders/' in url:
        return url.split('/folders/')[-1].split('?')[0]
    return url


def process_in_background(folder_id):
    """Background task to process photos."""
    global processing_state
    
    processing_state['is_processing'] = True
    processing_state['status'] = 'running'
    
    try:
        # Step 1: Download photos
        print(f"Starting download for folder: {folder_id}")
        update_progress('Connecting to Google Drive...', 0, 0)
        gdrive = WebGDriveHandler(socketio)
        
        update_progress('Downloading photos...', 0, 0)
        photo_paths = gdrive.download_folder(folder_id, 'downloads')
        
        print(f"Downloaded {len(photo_paths)} photos")
        
        if not photo_paths:
            update_progress('No photos found', 0, 0)
            processing_state['status'] = 'error'
            processing_state['is_processing'] = False
            return
        
        # Step 2: Process faces
        update_progress(f'Processing {len(photo_paths)} photos...', 0, len(photo_paths))
        processor = WebFaceProcessor(socketio)
        face_groups = processor.process_photos(photo_paths)
        
        print(f"Found {len(face_groups)} person groups")
        
        # Step 3: Organize
        update_progress('Organizing photos...', 0, 0)
        processor.organize_photos(face_groups, 'output')
        
        # Complete
        update_progress(f'Complete! Found {len(face_groups)} persons', len(photo_paths), len(photo_paths))
        processing_state['status'] = 'complete'
        processing_state['is_processing'] = False
        
    except Exception as e:
        print(f"ERROR in background process: {str(e)}")
        import traceback
        traceback.print_exc()
        update_progress(f'Error: {str(e)}', 0, 0)
        processing_state['status'] = 'error'
        processing_state['is_processing'] = False


def update_progress(step, progress, total):
    """Update progress and emit to clients."""
    global processing_state
    processing_state['current_step'] = step
    processing_state['progress'] = progress
    processing_state['total'] = total
    
    socketio.emit('progress', processing_state)


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
