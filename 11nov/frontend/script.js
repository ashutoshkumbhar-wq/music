document.addEventListener('DOMContentLoaded', () => {
    const sections = document.querySelectorAll('.section');
    const videos = document.querySelectorAll('.video-bg');
    let currentSectionIndex = 0;
    let isScrolling = false; 
    const scrollCooldown = 1000; // 1 second cooldown after scroll animation

    // === 1. Video Performance Optimization (Intersection Observer) ===
    
    // Configures the observer to check if 80% of the section is visible
    const observerOptions = {
      root: null, 
      rootMargin: '0px',
      threshold: 0.8 
    };

    const videoObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const video = entry.target.querySelector('.video-bg');
            if (!video) return;

            if (entry.isIntersecting) {
                // If visible, play the video
                video.play().catch(error => {
                    // Autoplay blocked warning
                    console.warn("Video autoplay blocked.", error);
                });
            } else {
                // If not visible, pause and rewind to save resources
                video.pause();
                video.currentTime = 0; 
            }
        });
    }, observerOptions);

    // Attach observer to each section
    sections.forEach(section => {
        videoObserver.observe(section);
    });


    // === 2. Strict Scroll Jacking Logic ===

    function scrollToSection(index) {
        const targetPosition = sections[index].offsetTop;
        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth' 
        });
    }

    window.addEventListener('wheel', (event) => {
        if (isScrolling) {
            return; 
        }
        event.preventDefault();
        isScrolling = true;

        const scrollDirection = event.deltaY;

        if (scrollDirection > 0) { // Scroll Down
            if (currentSectionIndex < sections.length - 1) {
                currentSectionIndex++;
            }
        } else { // Scroll Up
            if (currentSectionIndex > 0) {
                currentSectionIndex--;
            }
        }

        scrollToSection(currentSectionIndex);

        // Reset the cooldown flag after the animation time
        setTimeout(() => {
            isScrolling = false;
        }, scrollCooldown);

    }, { passive: false }); 


    // === 3. Section Click Navigation Logic ===

    const clickableSections = [
        { id: '#gesture', url: 'ge.html' },
        { id: '#data-powered', url: 'Cards/artist/index.html' },
        { id: '#style-radio', url: 'mood2/index.html' },
        { id: '#mood-radio', url: 'Fina/index.html' }
    ];

    clickableSections.forEach(item => {
        const section = document.querySelector(item.id);
        if (section) {
            section.addEventListener('click', () => {
                // Navigate when clicked
                window.location.href = item.url;
            });
        }
    });
});