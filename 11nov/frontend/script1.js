// ==============================
// Sidebar + Toggle Button Logic
// ==============================
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

 // Auto show/hide on scroll (20% of total page height)
window.addEventListener('scroll', () => {
  const scrollPosition = window.scrollY;
  const totalHeight = document.body.scrollHeight - window.innerHeight;
  const scrollPercent = (scrollPosition / totalHeight) * 100;

  if (scrollPercent > 20) {
    // Show sidebar + toggle
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
    // Hide sidebar + toggle
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


  // ==============================
  // Gesture Controller Setup
  // ==============================
  if (window.UnifiedGestureController) {
    window.gestureController = new UnifiedGestureController({
      backendUrl: 'http://localhost:3000',
      enableTouchGestures: true,
      enableCameraGestures: false,
      gestureThreshold: 0.3,
      cooldownMs: 1000,
    });

    const playPauseBtn = document.getElementById('play-pause-btn');
    const prevBtn = document.getElementById('prev-track-btn');
    const nextBtn = document.getElementById('next-track-btn');

    if (playPauseBtn) playPauseBtn.addEventListener('click', () => window.gestureController.togglePlayPause());
    if (prevBtn) prevBtn.addEventListener('click', () => window.gestureController.previousTrack());
    if (nextBtn) nextBtn.addEventListener('click', () => window.gestureController.nextTrack());

    // Gesture+Camera Toggle
    const toggleGestureCamera = document.getElementById('toggle-gesture-camera');
    if (toggleGestureCamera) {
      toggleGestureCamera.addEventListener('click', async () => {
        const touchEnabled = window.gestureController.options.enableTouchGestures;
        const camEnabled = window.gestureController.options.enableCameraGestures;
        const isEnabled = touchEnabled && camEnabled;

        if (isEnabled) {
          window.gestureController.options.enableTouchGestures = false;
          window.gestureController.options.enableCameraGestures = false;
          if (window.gestureController.gestureRecognition) {
            window.gestureController.gestureRecognition.destroy();
          }
          console.log('Gestures + Camera disabled');
        } else {
          window.gestureController.options.enableTouchGestures = true;
          window.gestureController.options.enableCameraGestures = true;
          await window.gestureController.initCameraGestures();
          console.log('Gestures + Camera enabled');
        }

        toggleGestureCamera.classList.toggle('active', !isEnabled);
      });
    }
  }

  // ==============================
  // Search Toggle
  // ==============================
  const searchToggle = document.getElementById('searchToggle');
  const searchContainer = document.getElementById('searchContainer');

  if (searchToggle && searchContainer) {
    searchToggle.addEventListener('click', () => {
      searchContainer.classList.toggle('active');
      const input = document.getElementById('searchInput');
      setTimeout(() => {
        if (searchContainer.classList.contains('active')) input.focus();
      }, 300);
    });

    document.addEventListener('click', (e) => {
      if (!searchContainer.contains(e.target) && e.target !== searchToggle) {
        searchContainer.classList.remove('active');
      }
    });
  }

  // ==============================
  // Audio Player Logic
  // ==============================
  const songs = [
    { title: "Track 1", artist: "Artist 1", src: "track1.mp3" },
    { title: "Track 2", artist: "Artist 2", src: "track2.mp3" },
    { title: "Track 3", artist: "Artist 3", src: "track3.mp3" }
  ];

  const audio = document.getElementById('audio');
  const playBtn = document.getElementById('play-btn');
  const nextBtn = document.getElementById('next-btn');
  const prevBtn = document.getElementById('prev-btn');
  const seek = document.getElementById('seek');
  const currentTime = document.getElementById('current-time');
  const duration = document.getElementById('duration');
  const muteBtn = document.getElementById('mute-btn');
  const volumeSlider = document.getElementById('volume');
  const maximizeBtn = document.getElementById('maximize-btn');
  const player = document.getElementById('audio-player');
  const container = player ? player.querySelector('.player-container') : null;

  let currentTrack = 0;
  let isPlaying = false;

  function loadTrack(index) {
    const song = songs[index];
    audio.src = song.src;
    currentTrack = index;
    audio.load();
  }

  function togglePlay() {
    if (audio.paused) {
      audio.play();
      isPlaying = true;
      playBtn.innerHTML = '<i class="fas fa-pause"></i>';
    } else {
      audio.pause();
      isPlaying = false;
      playBtn.innerHTML = '<i class="fas fa-play"></i>';
    }
  }

  function playTrack(index) {
    loadTrack(index);
    player.classList.remove('hidden');
    audio.play();
    isPlaying = true;
    playBtn.innerHTML = '<i class="fas fa-pause"></i>';
  }

  if (playBtn) playBtn.addEventListener('click', togglePlay);
  if (nextBtn) nextBtn.addEventListener('click', () => {
    currentTrack = (currentTrack + 1) % songs.length;
    playTrack(currentTrack);
  });
  if (prevBtn) prevBtn.addEventListener('click', () => {
    currentTrack = (currentTrack - 1 + songs.length) % songs.length;
    playTrack(currentTrack);
  });

  if (audio) {
    audio.addEventListener('timeupdate', () => {
      seek.value = (audio.currentTime / audio.duration) * 100 || 0;
      currentTime.textContent = formatTime(audio.currentTime);
      duration.textContent = formatTime(audio.duration);
    });
  }

  if (seek) {
    seek.addEventListener('input', () => {
      audio.currentTime = (seek.value / 100) * audio.duration;
    });
  }

  if (volumeSlider) {
    volumeSlider.addEventListener('input', () => {
      audio.volume = volumeSlider.value;
    });
  }

  if (muteBtn) {
    muteBtn.addEventListener('click', () => {
      audio.muted = !audio.muted;
      muteBtn.innerHTML = audio.muted
        ? '<i class="fas fa-volume-mute"></i>'
        : '<i class="fas fa-volume-up"></i>';
    });
  }

  if (maximizeBtn && container) {
    maximizeBtn.addEventListener('click', () => {
      container.classList.toggle('maximized');
      container.classList.toggle('mini');
    });
  }

  // Music card click
  document.querySelectorAll('.music-card').forEach((card) => {
    card.addEventListener('click', () => {
      const index = parseInt(card.dataset.index);
      if (!isNaN(index)) playTrack(index);
    });
  });

  function formatTime(sec) {
    if (isNaN(sec)) return '0:00';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }

  // ==============================
  // Playlist Modal
  // ==============================
  const addPlaylistBtn = document.getElementById('addPlaylistBtn');
  const playlistModal = document.getElementById('playlistModal');
  const closeModalBtn = document.getElementById('closeModalBtn');
  const addAnotherLinkBtn = document.getElementById('addAnotherLinkBtn');
  const playlistLinksContainer = document.getElementById('playlistLinksContainer');
  const savePlaylistsBtn = document.getElementById('savePlaylistsBtn');

  if (addPlaylistBtn && playlistModal) {
    addPlaylistBtn.addEventListener('click', () => playlistModal.classList.add('active'));
  }
  if (closeModalBtn) {
    closeModalBtn.addEventListener('click', () => playlistModal.classList.remove('active'));
  }
  const modalOverlay = document.querySelector('.modal-overlay');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', () => playlistModal.classList.remove('active'));
  }
  if (addAnotherLinkBtn && playlistLinksContainer) {
    addAnotherLinkBtn.addEventListener('click', () => {
      const newInput = document.createElement('input');
      newInput.type = 'text';
      newInput.classList.add('playlist-link');
      newInput.placeholder = 'Enter playlist link';
      playlistLinksContainer.appendChild(newInput);
    });
  }
  if (savePlaylistsBtn) {
    savePlaylistsBtn.addEventListener('click', () => {
      const links = Array.from(document.querySelectorAll('.playlist-link'))
        .map(input => input.value.trim())
        .filter(Boolean);
      console.log("User Playlist Links:", links);
      playlistModal.classList.remove('active');
    });
  }
  const toggle = document.getElementById('toggleSwitch');
const video = document.getElementById('cameraPreview');
let stream = null;

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    video.srcObject = stream;
    video.style.display = 'block'; // show video if you want
    console.log('Camera started');
  } catch (err) {
    console.error('Error accessing camera:', err);
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
    video.style.display = 'none';
    console.log('Camera stopped');
  }
}

toggle.addEventListener('click', async () => {
  toggle.classList.toggle('active');

  if (toggle.classList.contains('active')) {
    await startCamera();
  } else {
    stopCamera();
  }
});

  // ==============================
const spotifyStatus = document.getElementById('spotifyStatus');

spotifyStatus.addEventListener('click', () => {
  if (spotifyStatus.classList.contains('not-connected')) {
    window.location.href = 'profile.html';
  }
});

function setSpotifyStatus(isConnected) {
  if (isConnected) {
    spotifyStatus.classList.add('connected');
    spotifyStatus.classList.remove('not-connected');
    spotifyStatus.innerHTML = `
      <img src="https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg" alt="Spotify" class="spotify-logo" />
      <span class="status-text" style="color: green;">connected</span>
    `;
    spotifyStatus.style.cursor = 'default';
  } else {
    spotifyStatus.classList.add('not-connected');
    spotifyStatus.classList.remove('connected');
    spotifyStatus.innerHTML = `
      <img src="https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg" alt="Spotify" class="spotify-logo" />
      <span class="status-text" style="color: white;">not connected</span>
    `;
    spotifyStatus.style.cursor = 'pointer';
  }
}

// Initialize with not connected status
setSpotifyStatus(false);

});
