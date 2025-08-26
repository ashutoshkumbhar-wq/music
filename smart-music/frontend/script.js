document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const mainContainer = document.getElementById('main-container');
  const topSection = document.querySelector('.top-section');
  const toggleBtn = document.getElementById('sidebarToggle');

  let sidebarVisible = false;
  let toggleVisible = false;

  // Initial state
  sidebar.classList.remove('active');
  mainContainer.classList.remove('shifted');
  toggleBtn.textContent = '≡';
  toggleBtn.classList.remove('visible');

  // Manual toggle
  toggleBtn.addEventListener('click', () => {
    if (sidebarVisible) {
      sidebar.classList.remove('active');
      mainContainer.classList.remove('shifted');
      toggleBtn.textContent = '≡';
      sidebarVisible = false;
    } else {
      sidebar.classList.add('active');
      mainContainer.classList.add('shifted');
      toggleBtn.textContent = '⟨';
      sidebarVisible = true;
    }
  });

  // Auto show/hide on scroll
  window.addEventListener('scroll', () => {
    const threshold = topSection.offsetHeight;

    if (window.scrollY > threshold) {
      if (!toggleVisible) {
        toggleBtn.classList.add('visible');
        toggleVisible = true;
      }

      if (!sidebarVisible) {
        sidebar.classList.add('active');
        mainContainer.classList.add('shifted');
        toggleBtn.textContent = '⟨';
        sidebarVisible = true;
      }
    } else {
      if (toggleVisible) {
        toggleBtn.classList.remove('visible');
        toggleVisible = false;
      }

      if (sidebarVisible) {
        sidebar.classList.remove('active');
        mainContainer.classList.remove('shifted');
        toggleBtn.textContent = '≡';
        sidebarVisible = false;
      }
    }
  });
  const miniPlayPauseBtn = document.getElementById('mini-play-pause');
const miniTitle = document.getElementById('mini-title');

// Update mini-player state
function updateMiniPlayerUI() {
  miniTitle.textContent = currentTrack.title;
  miniPlayPauseBtn.innerHTML = isPlaying ? '<i class="fas fa-pause"></i>' : '<i class="fas fa-play"></i>';
}

// Event for minimized play/pause button
miniPlayPauseBtn.addEventListener('click', () => {
  if (isPlaying) {
    audio.pause();
  } else {
    audio.play();
  }
  updateMiniPlayerUI();
});

// Also call updateMiniPlayerUI in audio.onplay and audio.onpause
audio.addEventListener('play', updateMiniPlayerUI);
audio.addEventListener('pause', updateMiniPlayerUI);

});
