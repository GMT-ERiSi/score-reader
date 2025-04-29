/**
 * floating-logos.js
 * Creates an animated background with squadron logos floating around like in space
 */

// Class to manage floating logo objects
class FloatingLogo {
    constructor(container, imagePath, size = null) {
        this.container = container;
        this.element = document.createElement('div');
        this.element.className = 'floating-logo';
        
        // Create image element
        this.image = document.createElement('img');
        this.image.src = imagePath;
        this.image.alt = 'Squadron Logo';
        
        // Add error handling
        this.image.onerror = () => {
            console.error(`Failed to load logo image: ${imagePath}`);
        };
        
        this.image.onload = () => {
            console.log(`Successfully loaded logo: ${imagePath}`);
            this.setupLogo(size);
        };
        
        // Add to DOM
        this.element.appendChild(this.image);
        this.container.appendChild(this.element);
        
        // Placeholder values until image loads
        this.width = 50;
        this.height = 50;
        this.x = 0;
        this.y = 0;
        this.speedX = 0;
        this.speedY = 0;
        this.rotation = 0;
        this.rotationSpeed = 0;
        this.opacity = 0;
    }
    
    setupLogo(forcedSize) {
        // Set size based on original image size or forced size
        if (forcedSize) {
            this.width = forcedSize;
            this.height = forcedSize;
        } else {
            // Calculate size (120-200px) based on a weighted random value
            // with less variability in sizes - made twice as big
            const sizeWeight = Math.pow(Math.random(), 1.5); // Less bias toward smaller values
            this.width = 120 + Math.floor(sizeWeight * 80); // 120-200px range (doubled)
            this.height = this.width;
        }
        
        // Apply size to element
        this.image.style.width = `${this.width}px`;
        this.image.style.height = `${this.height}px`;
        
        // Set initial position (random position anywhere on screen)
        const containerRect = this.container.getBoundingClientRect();
        
        // Decide whether to start from an edge or somewhere on screen
        const startFromEdge = Math.random() < 0.7; // 70% chance to start from an edge
        
        if (startFromEdge) {
            // Pick a random edge (0=top, 1=right, 2=bottom, 3=left)
            const edge = Math.floor(Math.random() * 4);
            
            switch (edge) {
                case 0: // Top edge
                    this.x = Math.random() * containerRect.width;
                    this.y = -this.height;
                    break;
                case 1: // Right edge
                    this.x = containerRect.width + this.width;
                    this.y = Math.random() * containerRect.height;
                    break;
                case 2: // Bottom edge
                    this.x = Math.random() * containerRect.width;
                    this.y = containerRect.height + this.height;
                    break;
                case 3: // Left edge
                    this.x = -this.width;
                    this.y = Math.random() * containerRect.height;
                    break;
            }
        } else {
            // Start somewhere on screen
            this.x = Math.random() * containerRect.width;
            this.y = Math.random() * containerRect.height;
        }
        
        // Set random speed (0.1 - 0.7 pixels per frame) - slower for larger logos
        const baseSpeed = 0.1 + Math.random() * 0.6;
        
        // Direction vector (normalize to get consistent speed regardless of direction)
        const targetX = Math.random() * containerRect.width;
        const targetY = Math.random() * containerRect.height;
        
        // Calculate direction vector
        let dirX = targetX - this.x;
        let dirY = targetY - this.y;
        
        // Normalize the direction vector
        const length = Math.sqrt(dirX * dirX + dirY * dirY);
        dirX = dirX / length;
        dirY = dirY / length;
        
        // Apply speed in the calculated direction
        this.speedX = dirX * baseSpeed;
        this.speedY = dirY * baseSpeed;
        
        // Set random rotation speed (-0.5 to 0.5 degree per frame) - slower rotation for larger logos
        this.rotation = Math.random() * 360; // Initial rotation (0-360 degrees)
        this.rotationSpeed = -0.5 + Math.random() * 1.0; // Reduced rotation speed
        
        // Initial opacity (0.15 - 0.5) - more visible but still subtle
        this.opacity = 0.15 + Math.random() * 0.35;
        
        // Apply initial position, rotation and opacity
        this.updatePosition();
    }
    
    updatePosition() {
        // Apply current position, rotation and opacity to CSS
        this.element.style.transform = `translate(${this.x}px, ${this.y}px) rotate(${this.rotation}deg)`;
        this.element.style.opacity = this.opacity;
    }
    
    update() {
        // Update position
        this.x += this.speedX;
        this.y += this.speedY;
        
        // Update rotation
        this.rotation += this.rotationSpeed;
        
        // Check if logo is out of bounds
        const containerRect = this.container.getBoundingClientRect();
        const buffer = 250; // Larger extra space before considering out of bounds (for larger logos)
        
        if (this.x < -this.width - buffer || 
            this.x > containerRect.width + buffer || 
            this.y < -this.height - buffer || 
            this.y > containerRect.height + buffer) {
            
            // Reset to a new position on the opposite side
            if (Math.abs(this.speedX) > Math.abs(this.speedY)) {
                // Moving more horizontally
                this.x = (this.speedX > 0) ? -this.width : containerRect.width;
                this.y = Math.random() * containerRect.height;
            } else {
                // Moving more vertically
                this.x = Math.random() * containerRect.width;
                this.y = (this.speedY > 0) ? -this.height : containerRect.height;
            }
            
            // Slightly change speed and rotation on reset
            this.speedX *= 0.8 + Math.random() * 0.4; // 80-120% of current speed
            this.speedY *= 0.8 + Math.random() * 0.4;
            this.rotationSpeed = -0.5 + Math.random() * 1.0; // Slower rotation
            
            // Ensure we don't slow down too much
            const minSpeed = 0.1; // Lower minimum speed for larger logos
            const currentSpeed = Math.sqrt(this.speedX * this.speedX + this.speedY * this.speedY);
            if (currentSpeed < minSpeed) {
                // Normalize then set to minimum speed
                this.speedX = (this.speedX / currentSpeed) * minSpeed;
                this.speedY = (this.speedY / currentSpeed) * minSpeed;
            }
            
            // Random opacity again
            this.opacity = 0.15 + Math.random() * 0.35;
        }
        
        // Update the visual position
        this.updatePosition();
    }
}

// Class to manage the background animation
class FloatingLogosBackground {
    constructor(containerId = 'floating-logos-container') {
        // Create container if it doesn't exist
        if (!document.getElementById(containerId)) {
            const container = document.createElement('div');
            container.id = containerId;
            container.className = 'floating-logos-container';
            
            // Style the container to cover the whole viewport
            container.style.position = 'fixed';
            container.style.top = '0';
            container.style.left = '0';
            container.style.width = '100vw';
            container.style.height = '100vh';
            container.style.zIndex = '-1'; // Behind all content
            container.style.overflow = 'hidden';
            container.style.pointerEvents = 'none'; // Don't interfere with clicks
            
            // Add to body as first child to be behind everything
            document.body.insertBefore(container, document.body.firstChild);
            
            // Create Death Star background element
            const deathStar = document.createElement('div');
            deathStar.className = 'death-star-bg';
            
            // Alternative approach: use an img element instead of background-image
            const deathStarImg = document.createElement('img');
            deathStarImg.src = 'images/Death Star.png';
            deathStarImg.style.width = '110%';
            deathStarImg.style.height = '110%';
            deathStarImg.style.objectFit = 'contain';
            deathStar.appendChild(deathStarImg);
            
            document.body.insertBefore(deathStar, document.body.firstChild);
        }
        
        this.container = document.getElementById(containerId);
        this.logos = []; // Will hold all floating logo objects
        this.animationId = null; // For the animation frame
        this.logoImages = []; // Will be populated with available logo images
        this.paused = false;
    }
    
    loadImages() {
        // List of all squadron logo images in the images folder
        this.logoImages = [
            'images/cavern-angels-blue-squadron.png',
            'images/gray-hell-porgs.png',
            'images/hive-guard.png',
            'images/Idiots_Array.png',
            'images/kintan.png',
            'images/LSS_Black_Sabacc_logo_O_5000px_FINAL.png',
            'images/Remnant Squadron Gold Stars.png',
            'images/sabacc_emblem.png',
            'images/siren3.png',
            'images/tangerine-squadron.png',
            'images/TRA.png',
            'images/the-randolorians.png'
        ];
        
        // Make sure the Remnant Squadron is included
        // Shuffle the array to get random order
        // this.shuffleArray(this.logoImages); // Temporarily disabled shuffling to ensure all logos appear
        
        return this;
    }
    
    shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }
    
    start(logoCount = 15) {
        // Make sure we have images loaded
        if (this.logoImages.length === 0) {
            this.loadImages();
        }
        
        // Clear any existing logos
        this.stop();
        this.container.innerHTML = '';
        this.logos = [];
        
        // Create the logos
        for (let i = 0; i < logoCount; i++) {
            // Cycle through available logos if we need more than we have images
            const imageIndex = i % this.logoImages.length;
            const imagePath = this.logoImages[imageIndex];
            
            // Log which images are being used
            console.log(`Creating logo ${i+1}/${logoCount}: ${imagePath}`);
            
            const logo = new FloatingLogo(this.container, imagePath);
            this.logos.push(logo);
        }
        
        // Start animation
        this.animate();
        
        // Add resize event listener to handle window resizing
        window.addEventListener('resize', this.handleResize.bind(this));
        
        return this;
    }
    
    animate() {
        if (!this.paused) {
            // Update each logo
            this.logos.forEach(logo => logo.update());
        }
        
        // Continue animation loop
        this.animationId = requestAnimationFrame(this.animate.bind(this));
    }
    
    stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        return this;
    }
    
    pause() {
        this.paused = true;
        return this;
    }
    
    resume() {
        this.paused = false;
        return this;
    }
    
    handleResize() {
        // When window is resized, reset all logos to make sure they're positioned correctly
        this.logos.forEach(logo => logo.setupLogo());
    }
}

// Start the animation when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Remove existing star background if it exists
    const stars = document.querySelectorAll('.star');
    stars.forEach(star => star.remove());
    
    // Create the floating logos background with 12 logos (show all available logos)
    window.logosBackground = new FloatingLogosBackground().start(12);
    
    // Set the background to black
    document.body.style.backgroundColor = '#000';
});
