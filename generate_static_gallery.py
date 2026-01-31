"""
Static Gallery Generator
Creates a modern, responsive HTML gallery for the organized photos.
"""

import os
import json

GALLERY_ROOT = "gallery"
FOLDERS = [
    {"id": "haldi", "name": "✨ Haldi Ceremony", "desc": "Yellow hues & joyful beginnings"},
    {"id": "ring", "name": "💍 Ring Ceremony", "desc": "Engagement highlights"},
    {"id": "rituals", "name": "🔥 Rituals", "desc": "Traditional moments"},
    {"id": "wedding", "name": "💒 The Wedding", "desc": "The big day"}
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wedding Gallery</title>
    <link rel="stylesheet" href="css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
</head>
<body>
    <div id="app">
        <header class="main-header">
            <h1>Wedding Gallery</h1>
            <p>A collection of beautiful moments</p>
        </header>

        <main class="gallery-grid">
            {folder_cards}
        </main>
        
        <footer class="main-footer">
            <p>Built with ❤️ using AI Photo Sorter</p>
        </footer>
    </div>
</body>
</html>"""

FOLDER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{folder_name} - Gallery</title>
    <link rel="stylesheet" href="../css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
</head>
<body>
    <div class="folder-page">
        <header class="folder-header">
            <a href="../index.html" class="back-link">← Back to Albums</a>
            <h1>{folder_name}</h1>
            <p>{total_people} People found</p>
        </header>

        <div class="people-container">
            {people_sections}
        </div>
    </div>

    <!-- Lightbox -->
    <div id="lightbox" class="lightbox">
        <span class="close">&times;</span>
        <img class="lightbox-content" id="lightbox-img">
        <a id="download-btn" class="download-btn" href="" download>Download</a>
        <div class="nav-btn prev" onclick="changeImage(-1)">❮</div>
        <div class="nav-btn next" onclick="changeImage(1)">❯</div>
    </div>

    <script src="../js/gallery.js"></script>
</body>
</html>"""

CSS_CONTENT = """
:root {
    --bg-color: #0f1014;
    --card-bg: #1e1f24;
    --text-primary: #ffffff;
    --text-secondary: #a0a0a0;
    --accent: #f39c12;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    background-color: var(--bg-color);
    color: var(--text-primary);
    font-family: 'Outfit', sans-serif;
    min-height: 100vh;
}

/* Home Page */
.main-header {
    text-align: center;
    padding: 60px 20px;
    background: linear-gradient(180deg, rgba(30,31,36,0) 0%, rgba(30,31,36,0.3) 100%);
}
.main-header h1 { font-size: 3rem; margin-bottom: 10px; background: linear-gradient(90deg, #f39c12, #e74c3c); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.main-header p { color: var(--text-secondary); font-size: 1.2rem; }

.gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 30px;
    padding: 20px 5%;
    max-width: 1400px;
    margin: 0 auto;
}

.folder-card {
    background: var(--card-bg);
    border-radius: 20px;
    padding: 30px;
    text-align: center;
    text-decoration: none;
    color: inherit;
    transition: transform 0.3s, box-shadow 0.3s;
    border: 1px solid rgba(255,255,255,0.05);
}
.folder-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    border-color: var(--accent);
}
.folder-card h2 { font-size: 1.8rem; margin-bottom: 10px; color: var(--accent); }
.folder-card p { color: var(--text-secondary); }

/* Folder Page */
.folder-header {
    background: rgba(0,0,0,0.3);
    padding: 30px 5%;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255,255,255,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.back-link { color: var(--text-secondary); text-decoration: none; font-weight: 600; font-size: 1.1rem; }
.back-link:hover { color: var(--text-primary); }

.people-container {
    padding: 40px 5%;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 30px;
}

.person-group {
    background: var(--card-bg);
    border-radius: 16px;
    overflow: hidden;
    padding: 20px;
}

.person-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;
}
.avatar {
    width: 60px; height: 60px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid var(--accent);
}
.person-info h3 { color: var(--text-primary); }
.person-info p { color: var(--text-secondary); font-size: 0.9rem; }

.photo-grid {
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding-bottom: 10px;
    scrollbar-width: thin;
    scrollbar-color: var(--accent) var(--card-bg);
}
.photo-grid::-webkit-scrollbar { height: 6px; }
.photo-grid::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 3px; }

.photo-thumb {
    height: 120px;
    width: auto;
    border-radius: 8px;
    cursor: pointer;
    transition: opacity 0.2s;
}
.photo-thumb:hover { opacity: 0.8; }

/* Lightbox */
.lightbox {
    display: none;
    position: fixed;
    z-index: 999;
    left: 0; top: 0;
    width: 100%; height: 100%;
    background-color: rgba(0,0,0,0.95);
    justify-content: center;
    align-items: center;
}
.lightbox-content {
    max-width: 90%;
    max-height: 90%;
    border-radius: 4px;
    box-shadow: 0 0 50px rgba(0,0,0,0.5);
}
.close {
    position: absolute;
    top: 20px; right: 35px;
    color: #f1f1f1;
    font-size: 40px;
    font-weight: bold;
    cursor: pointer;
}
.nav-btn {
    position: absolute;
    top: 50%;
    width: auto;
    padding: 16px;
    margin-top: -50px;
    color: white;
    font-weight: bold;
    font-size: 30px;
    cursor: pointer;
    user-select: none;
    background: rgba(0,0,0,0.3);
    border-radius: 50%;
    transition: 0.3s;
}
.prev { left: 20px; }
.next { right: 20px; }
.nav-btn:hover { background: rgba(255,255,255,0.2); }

.download-btn {
    position: absolute;
    bottom: 30px;
    background: var(--accent);
    color: white;
    padding: 10px 20px;
    border-radius: 20px;
    text-decoration: none;
    font-weight: 600;
}
"""

JS_CONTENT = """
// Gallery navigation logic
let currentImages = [];
let currentIndex = 0;

function openLightbox(imgSrc, groupImages) {
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const downloadBtn = document.getElementById('download-btn');
    
    lightbox.style.display = "flex";
    lightboxImg.src = imgSrc;
    downloadBtn.href = imgSrc;
    
    // Set context for navigation
    currentImages = groupImages; // Array of image URLs
    currentIndex = currentImages.indexOf(imgSrc);
}

function changeImage(n) {
    currentIndex += n;
    if (currentIndex >= currentImages.length) currentIndex = 0;
    if (currentIndex < 0) currentIndex = currentImages.length - 1;
    
    const newSrc = currentImages[currentIndex];
    document.getElementById('lightbox-img').src = newSrc;
    document.getElementById('download-btn').href = newSrc;
}

// Global click handler for delegated events
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('photo-thumb')) {
        // Collect all images in this person's group
        const groupContainer = e.target.closest('.photo-grid');
        const images = Array.from(groupContainer.querySelectorAll('.photo-thumb'))
                            .map(img => img.dataset.full); // Use data-full for high res
        
        openLightbox(e.target.dataset.full, images);
    }
    
    if (e.target.classList.contains('close') || e.target.id === 'lightbox') {
        document.getElementById('lightbox').style.display = "none";
    }
});

// Keyboard navigation
document.addEventListener('keydown', function(e) {
    if (document.getElementById('lightbox').style.display === "flex") {
        if (e.key === "ArrowLeft") changeImage(-1);
        if (e.key === "ArrowRight") changeImage(1);
        if (e.key === "Escape") document.getElementById('lightbox').style.display = "none";
    }
});
"""

def generate_index():
    """Generate main index.html"""
    cards_html = ""
    for folder in FOLDERS:
        cards_html += f"""
        <a href="{folder['id']}/index.html" class="folder-card">
            <h2>{folder['name']}</h2>
            <p>{folder['desc']}</p>
        </a>
        """
    
    content = HTML_TEMPLATE.replace("{folder_cards}", cards_html)
    with open(os.path.join(GALLERY_ROOT, "index.html"), "w") as f:
        f.write(content)

def generate_folder_pages():
    """Generate page for each folder."""
    for folder in FOLDERS:
        folder_id = folder['id']
        folder_path = os.path.join(GALLERY_ROOT, folder_id)
        
        if not os.path.exists(folder_path):
            continue
            
        # Scan for people
        people_html = ""
        people = []
        
        for person_id in sorted(os.listdir(folder_path)):
            person_dir = os.path.join(folder_path, person_id)
            if not os.path.isdir(person_dir):
                continue
            
            photos = [f for f in os.listdir(person_dir) if f.startswith('thumb_')]
            has_avatar = os.path.exists(os.path.join(person_dir, '_avatar.jpg'))
            
            # Sort photos to match original order if possible, or name
            photos.sort()
            
            people.append({
                "id": person_id,
                "count": len(photos),
                "avatar": has_avatar,
                "thumbs": photos
            })
            
        # Sort people by photo count
        people.sort(key=lambda x: x['count'], reverse=True)
        
        for p in people:
            avatar_src = f"{p['id']}/_avatar.jpg" if p['avatar'] else "../assets/default_avatar.png"
            
            photos_html = ""
            for thumb in p['thumbs']:
                full_img = thumb.replace('thumb_', '')
                photos_html += f"""
                <img class="photo-thumb" 
                     src="{p['id']}/{thumb}" 
                     data-full="{p['id']}/{full_img}" 
                     loading="lazy" 
                     alt="Photo">
                """
            
            people_html += f"""
            <div class="person-group">
                <div class="person-header">
                    <img class="avatar" src="{avatar_src}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIiBmaWxsPSIjMzMzIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI1MCIvPjwvc3ZnPg=='">
                    <div class="person-info">
                        <h3>{p['id'].replace('_', ' ')}</h3>
                        <p>{p['count']} Photos</p>
                    </div>
                </div>
                <div class="photo-grid">
                    {photos_html}
                </div>
            </div>
            """
            
        content = FOLDER_TEMPLATE.format(
            folder_name=folder['name'],
            total_people=len(people),
            people_sections=people_html
        )
        
        with open(os.path.join(folder_path, "index.html"), "w") as f:
            f.write(content)

def main():
    print("Generating static gallery...")
    
    # Create structure
    os.makedirs(os.path.join(GALLERY_ROOT, "css"), exist_ok=True)
    os.makedirs(os.path.join(GALLERY_ROOT, "js"), exist_ok=True)
    
    # Write assets
    with open(os.path.join(GALLERY_ROOT, "css", "style.css"), "w") as f:
        f.write(CSS_CONTENT)
        
    with open(os.path.join(GALLERY_ROOT, "js", "gallery.js"), "w") as f:
        f.write(JS_CONTENT)
        
    # Generate pages
    generate_index()
    generate_folder_pages()
    
    print("✓ Static gallery generated in 'gallery/'")
    print("  You can now deploy this folder to GitHub Pages!")

if __name__ == "__main__":
    main()
