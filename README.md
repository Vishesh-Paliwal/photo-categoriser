# Photo Face Recognition App

An application that downloads photos from Google Drive folders and organizes them by detected faces.

## Features
- 🌐 Web interface with real-time progress tracking
- 📥 Downloads photos from nested Google Drive folders
- 🤖 Detects and recognizes faces using DeepFace
- 📁 Organizes photos by person into separate folders
- 💾 Download organized photos as ZIP
- ⚡ Handles large photo collections efficiently

## Quick Start (Web Version - Recommended)

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements-web.txt
```

3. Run the web app:
```bash
python app.py
```

4. Open browser to `http://localhost:5000`

5. Paste your Google Drive folder link and click "Start Processing"

**Note:** Works with publicly shared Google Drive folders - no authentication required!

## CLI Version

For command-line usage:
```bash
pip install -r requirements.txt
python main.py
```

## How It Works

1. **Download**: Recursively downloads all images from Google Drive folder
2. **Detect**: Uses DeepFace with FaceNet model to detect faces
3. **Group**: Groups similar faces using cosine similarity
4. **Organize**: Copies photos to person-specific folders

## Output Structure

```
output/
├── Person_1/
│   ├── photo1.jpg
│   └── photo2.jpg
├── Person_2/
│   └── photo3.jpg
└── unknown/  (photos with no faces detected)
```

## Large Photo Collections

The web version handles large collections efficiently:
- Progress updates every 5 photos
- Batch processing to prevent memory issues
- Background processing with real-time status
- Download results as ZIP file

## Troubleshooting

**DeepFace installation issues:**
```bash
pip install --upgrade pip
pip install deepface --no-cache-dir
```

**Port already in use:**
```bash
# Change port in app.py
socketio.run(app, port=5001)
```
