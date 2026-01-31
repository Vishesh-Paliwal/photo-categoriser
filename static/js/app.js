// Initialize Socket.IO
const socket = io();

// UI Elements
const processBtn = document.getElementById('process-btn');
const statusSection = document.getElementById('status-section');
const resultsSection = document.getElementById('results-section');
const errorSection = document.getElementById('error-section');
const statusIcon = document.getElementById('status-icon');
const statusText = document.getElementById('status-text');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');

// Listen for progress updates
socket.on('progress', (data) => {
    updateProgress(data);
});

function startProcessing() {
    const url = document.getElementById('gdrive-url').value.trim();
    
    if (!url) {
        alert('Please enter a Google Drive folder link');
        return;
    }
    
    // Reset UI
    hideAll();
    statusSection.classList.remove('hidden');
    processBtn.disabled = true;
    statusIcon.textContent = '⏳';
    statusIcon.classList.add('spinning');
    statusText.textContent = 'Starting...';
    
    // Start processing
    fetch('/api/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: url })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
        }
    })
    .catch(error => {
        showError(error.message);
    });
}

function updateProgress(data) {
    statusText.textContent = data.current_step;
    
    if (data.total > 0) {
        const percentage = (data.progress / data.total) * 100;
        progressBar.style.width = percentage + '%';
        progressText.textContent = `${data.progress} / ${data.total}`;
    } else {
        progressText.textContent = data.current_step;
    }
    
    // Check if complete
    if (data.status === 'complete') {
        statusIcon.classList.remove('spinning');
        statusIcon.textContent = '✅';
        
        setTimeout(() => {
            hideAll();
            showResults(data);
        }, 1000);
    } else if (data.status === 'error') {
        statusIcon.classList.remove('spinning');
        showError(data.current_step);
    }
}

function showResults(data) {
    resultsSection.classList.remove('hidden');
    
    const summary = document.getElementById('results-summary');
    const personCount = data.current_step.match(/Found (\d+) persons/);
    
    if (personCount) {
        summary.textContent = `Successfully organized photos into ${personCount[1]} person folders!`;
    } else {
        summary.textContent = 'Photos have been organized by detected faces!';
    }
    
    // Load and display gallery
    loadGallery();
    
    processBtn.disabled = false;
}

function loadGallery() {
    fetch('/api/results')
        .then(response => response.json())
        .then(data => {
            displayGallery(data);
        })
        .catch(error => {
            console.error('Error loading gallery:', error);
        });
}

function displayGallery(results) {
    const container = document.getElementById('gallery-container');
    container.innerHTML = '';
    
    // Sort persons (unknown last)
    const persons = Object.keys(results).sort((a, b) => {
        if (a === 'unknown') return 1;
        if (b === 'unknown') return -1;
        return a.localeCompare(b);
    });
    
    persons.forEach(person => {
        const personData = results[person];
        
        const personDiv = document.createElement('div');
        personDiv.className = 'person-group';
        
        personDiv.innerHTML = `
            <div class="person-header">
                <div>
                    <div class="person-title">${person}</div>
                    <div class="person-count">${personData.count} photo${personData.count !== 1 ? 's' : ''}</div>
                </div>
                <button class="download-person-btn" onclick="downloadPerson('${person}')">
                    📥 Download All
                </button>
            </div>
            <div class="photo-grid" id="grid-${person}"></div>
        `;
        
        container.appendChild(personDiv);
        
        // Add photos to grid
        const grid = document.getElementById(`grid-${person}`);
        personData.photos.forEach(photo => {
            const photoDiv = document.createElement('div');
            photoDiv.className = 'photo-item';
            photoDiv.innerHTML = `
                <img src="${photo.url}" alt="${photo.filename}" onclick="openModal('${photo.url}')">
                <div class="photo-overlay">
                    <button class="photo-download-btn" onclick="downloadPhoto('${person}', '${photo.filename}')">
                        📥 Download
                    </button>
                </div>
            `;
            grid.appendChild(photoDiv);
        });
    });
    
    // Add modal for full-size view
    if (!document.getElementById('photo-modal')) {
        const modal = document.createElement('div');
        modal.id = 'photo-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <img class="modal-content" id="modal-img">
        `;
        document.body.appendChild(modal);
    }
}

function openModal(imageUrl) {
    const modal = document.getElementById('photo-modal');
    const modalImg = document.getElementById('modal-img');
    modal.classList.add('active');
    modalImg.src = imageUrl;
}

function closeModal() {
    const modal = document.getElementById('photo-modal');
    modal.classList.remove('active');
}

function downloadPerson(person) {
    window.location.href = `/api/download/person/${person}`;
}

function downloadPhoto(person, filename) {
    event.stopPropagation(); // Prevent opening modal
    window.location.href = `/api/download/photo/${person}/${filename}`;
}

function showError(message) {
    hideAll();
    errorSection.classList.remove('hidden');
    document.getElementById('error-message').textContent = message;
    processBtn.disabled = false;
}

function hideAll() {
    statusSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');
}

function downloadResults() {
    window.location.href = '/api/download';
}

function cleanup() {
    if (!confirm('This will delete all downloaded and processed files. Continue?')) {
        return;
    }
    
    fetch('/api/cleanup', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        alert('Cleanup complete!');
        resetApp();
    })
    .catch(error => {
        alert('Error during cleanup: ' + error.message);
    });
}

function resetApp() {
    hideAll();
    closeModal();
    processBtn.disabled = false;
    progressBar.style.width = '0%';
    progressText.textContent = '0 / 0';
    document.getElementById('gallery-container').innerHTML = '';
}

// Close modal on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// Close modal on background click
document.addEventListener('click', (e) => {
    const modal = document.getElementById('photo-modal');
    if (modal && e.target === modal) {
        closeModal();
    }
});

// Check status on page load
window.addEventListener('load', () => {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (data.is_processing) {
                statusSection.classList.remove('hidden');
                processBtn.disabled = true;
            }
        });
});
