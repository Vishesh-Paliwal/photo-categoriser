// Gallery state
let galleryData = {};
let currentPerson = null;
let currentPhotoIndex = 0;
let currentPersonPhotos = [];

// Load gallery on page load
window.addEventListener('load', loadGallery);

function loadGallery() {
    fetch('/api/gallery')
        .then(response => response.json())
        .then(data => {
            galleryData = data;
            displayPersonsGrid(data);
            document.getElementById('loading').classList.add('hidden');
            document.getElementById('gallery-container').classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error loading gallery:', error);
            document.getElementById('loading').innerHTML = '<p>Error loading gallery</p>';
        });
}

function displayPersonsGrid(data) {
    const container = document.getElementById('persons-grid');
    container.innerHTML = '';
    
    // Sort persons (unknown last)
    const persons = Object.keys(data).sort((a, b) => {
        if (a === 'unknown') return 1;
        if (b === 'unknown') return -1;
        return a.localeCompare(b, undefined, { numeric: true });
    });
    
    if (persons.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 40px;">No photos found</p>';
        return;
    }
    
    persons.forEach(person => {
        const personData = data[person];
        
        const personCard = document.createElement('div');
        personCard.className = 'person-card';
        personCard.onclick = () => showPersonPhotos(person);
        
        personCard.innerHTML = `
            <img src="${personData.avatar}" alt="${person}" class="person-avatar">
            <div class="person-name">${person}</div>
            <div class="person-photo-count">${personData.count} photo${personData.count !== 1 ? 's' : ''}</div>
        `;
        
        container.appendChild(personCard);
    });
}

function showPersonPhotos(person) {
    currentPerson = person;
    const personData = galleryData[person];
    
    // Hide persons grid, show person photos
    document.getElementById('persons-grid').classList.add('hidden');
    document.getElementById('person-photos').classList.remove('hidden');
    
    // Update header
    document.getElementById('current-person-name').textContent = person;
    document.getElementById('download-current-person').onclick = () => downloadPerson(person);
    
    // Display photos
    const grid = document.getElementById('photos-grid');
    grid.innerHTML = '';
    
    personData.photos.forEach((photo, index) => {
        const photoDiv = document.createElement('div');
        photoDiv.className = 'photo-item';
        photoDiv.onclick = () => openModal(person, index);
        
        const img = document.createElement('img');
        img.src = photo.url;
        img.alt = photo.filename;
        img.loading = 'lazy';
        
        photoDiv.appendChild(img);
        grid.appendChild(photoDiv);
    });
    
    // Scroll to top
    window.scrollTo(0, 0);
}

function showPersonsGrid() {
    document.getElementById('person-photos').classList.add('hidden');
    document.getElementById('persons-grid').classList.remove('hidden');
    currentPerson = null;
    window.scrollTo(0, 0);
}

function openModal(person, photoIndex) {
    const modal = document.getElementById('photo-modal');
    const modalImg = document.getElementById('modal-img');
    const modalInfo = document.getElementById('modal-info');
    
    currentPersonPhotos = galleryData[person].photos;
    currentPhotoIndex = photoIndex;
    
    const photo = currentPersonPhotos[currentPhotoIndex];
    
    modal.classList.add('active');
    modalImg.src = photo.url;
    modalInfo.textContent = `${person} - ${currentPhotoIndex + 1} / ${currentPersonPhotos.length}`;
    
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    const modal = document.getElementById('photo-modal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
}

function navigatePhoto(direction) {
    currentPhotoIndex += direction;
    
    // Wrap around
    if (currentPhotoIndex < 0) {
        currentPhotoIndex = currentPersonPhotos.length - 1;
    } else if (currentPhotoIndex >= currentPersonPhotos.length) {
        currentPhotoIndex = 0;
    }
    
    const modalImg = document.getElementById('modal-img');
    const modalInfo = document.getElementById('modal-info');
    const photo = currentPersonPhotos[currentPhotoIndex];
    
    modalImg.src = photo.url;
    
    // Extract person name from current modal info
    const currentInfo = modalInfo.textContent;
    const person = currentInfo.split(' - ')[0];
    modalInfo.textContent = `${person} - ${currentPhotoIndex + 1} / ${currentPersonPhotos.length}`;
}

function downloadPerson(person) {
    window.location.href = `/api/download/person/${person}`;
}

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    const modal = document.getElementById('photo-modal');
    
    if (modal.classList.contains('active')) {
        if (e.key === 'Escape') {
            closeModal();
        } else if (e.key === 'ArrowLeft') {
            navigatePhoto(-1);
        } else if (e.key === 'ArrowRight') {
            navigatePhoto(1);
        }
    }
});

// Close modal on background click
document.getElementById('photo-modal').addEventListener('click', (e) => {
    if (e.target.id === 'photo-modal') {
        closeModal();
    }
});
