// ===============================================
// --- UI INTERACTIVITY LOGIC ---
// ===============================================
document.addEventListener('DOMContentLoaded', () => {
    // Get references to the necessary HTML elements
    const artistInput = document.getElementById('artist-input');
    const addArtistBtn = document.getElementById('add-artist-btn');
    const selectedArtistsBox = document.getElementById('selected-artists-box');
    const placeholderText = document.getElementById('placeholder-text');

    // Function to update the visibility of the placeholder text
    const updatePlaceholderVisibility = () => {
        // If there are any elements besides the placeholder, hide it. Otherwise, show it.
        const hasPills = selectedArtistsBox.querySelector('.artist-pill');
        placeholderText.style.display = hasPills ? 'none' : 'block';
    };

    // Function to add an artist pill
    const addArtist = () => {
        const artistName = artistInput.value.trim(); // Get value and remove whitespace

        // Only add if the input is not empty
        if (artistName) {
            // 1. Create the pill element
            const pill = document.createElement('div');
            pill.className = 'artist-pill';
            pill.textContent = artistName;

            // 2. Create the remove 'x'
            const removeBtn = document.createElement('span');
            removeBtn.className = 'remove-btn';
            removeBtn.innerHTML = '&times;'; // The 'x' character

            // 3. Add the remove button to the pill
            pill.appendChild(removeBtn);

            // 4. Add the complete pill to the selection box
            selectedArtistsBox.appendChild(pill);
            
            // 5. Clear the input field
            artistInput.value = '';

            // 6. Update placeholder visibility
            updatePlaceholderVisibility();

            // 7. Add an event listener to the pill to remove it on click
            pill.addEventListener('click', () => {
                pill.remove();
                updatePlaceholderVisibility(); // Check again after removing
            });
        }
    };

    // Event listener for the add button
    addArtistBtn.addEventListener('click', addArtist);

    // Event listener to also add artist when 'Enter' is pressed in the input field
    artistInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevents form submission if it's in a form
            addArtist();
        }
    });

    // Initial check in case you have pre-loaded artists
    updatePlaceholderVisibility();
});


// ===================================================================
// --- BACKGROUND ANIMATION LOGIC (CONSTELLATION EFFECT) ---
// ===================================================================

const canvas = document.getElementById('background-animation');
const ctx = canvas.getContext('2d');
let particlesArray;

// Set canvas size to full screen
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

// Particle class
class Particle {
    constructor(x, y, directionX, directionY, size, color) {
        this.x = x;
        this.y = y;
        this.directionX = directionX;
        this.directionY = directionY;
        this.size = size;
        this.color = color;
    }
    // Method to draw individual particle
    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2, false);
        ctx.fillStyle = this.color;
        ctx.fill();
    }
    // Method to update particle position and handle wall collision
    update() {
        if (this.x > canvas.width || this.x < 0) {
            this.directionX = -this.directionX;
        }
        if (this.y > canvas.height || this.y < 0) {
            this.directionY = -this.directionY;
        }
        this.x += this.directionX;
        this.y += this.directionY;
        this.draw();
    }
}

// Create particle array
function init() {
    particlesArray = [];
    let numberOfParticles = (canvas.height * canvas.width) / 9000;
    for (let i = 0; i < numberOfParticles; i++) {
        let size = (Math.random() * 2) + 1;
        let x = (Math.random() * ((innerWidth - size * 2) - (size * 2)) + size * 2);
        let y = (Math.random() * ((innerHeight - size * 2) - (size * 2)) + size * 2);
        let directionX = (Math.random() * .4) - .2;
        let directionY = (Math.random() * .4) - .2;
        // Use a greenish color palette to match the theme
        let hue = 140 + (Math.random() * 40); // Hues around green
        let saturation = 50 + (Math.random() * 30); // 50-80% saturation
        let lightness = 40 + (Math.random() * 20); // 40-60% lightness
        let color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;

        particlesArray.push(new Particle(x, y, directionX, directionY, size, color));
    }
}

// Function to draw lines between nearby particles
function connect() {
    let opacityValue = 1;
    for (let a = 0; a < particlesArray.length; a++) {
        for (let b = a; b < particlesArray.length; b++) {
            let distance = ((particlesArray[a].x - particlesArray[b].x) * (particlesArray[a].x - particlesArray[b].x)) 
                         + ((particlesArray[a].y - particlesArray[b].y) * (particlesArray[a].y - particlesArray[b].y));
            if (distance < (canvas.width/7) * (canvas.height/7)) {
                opacityValue = 1 - (distance/20000);
                let avgHue = (parseFloat(particlesArray[a].color.match(/hsl\((\d+)/)[1]) + parseFloat(particlesArray[b].color.match(/hsl\((\d+)/)[1])) / 2;
                ctx.strokeStyle = `hsla(${avgHue}, 50%, 50%, ${opacityValue})`;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(particlesArray[a].x, particlesArray[a].y);
                ctx.lineTo(particlesArray[b].x, particlesArray[b].y);
                ctx.stroke();
            }
        }
    }
}

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    ctx.clearRect(0, 0, innerWidth, innerHeight);

    for (let i = 0; i < particlesArray.length; i++) {
        particlesArray[i].update();
    }
    connect();
}

// Resize event listener
window.addEventListener('resize', () => {
    canvas.width = innerWidth;
    canvas.height = innerHeight;
    init();
});
document.addEventListener("DOMContentLoaded", () => {
    const playBtn = document.querySelector(".btn-play");

    playBtn.addEventListener("click", () => {
        // Redirect to your page
        window.location.href = "Frame/index.html";
    });
});
document.addEventListener("DOMContentLoaded", () => {
    const playRandomBtn = document.querySelector(".btn.btn-green:not(.btn-arrow):not(.btn-play)");

    if (playRandomBtn) {
        playRandomBtn.addEventListener("click", () => {
            window.location.href = "random/index.html"; 
        });
    }
});



// Initial setup
init();
animate();