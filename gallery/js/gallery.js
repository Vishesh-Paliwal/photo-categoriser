
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
