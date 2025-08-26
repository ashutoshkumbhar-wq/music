// Floating images array — replace these URLs with your own image links
const imageUrls = [
  "profile img/img1.png",
  "profile img/img2.png"
];

const container = document.getElementById('notes');

// Generate floating images
for (let i = 0; i < 20; i++) {
  const note = document.createElement('div');
  note.classList.add('note');

  const img = document.createElement('img');
  img.src = imageUrls[Math.floor(Math.random() * imageUrls.length)];

  note.style.left = Math.random() * 100 + 'vw';
  note.style.animationDuration = (4 + Math.random() * 4) + 's';

  note.appendChild(img);
  container.appendChild(note);
}

// Backend API configuration
const BACKEND_URL = 'http://localhost:5000';

// Spotify OAuth Config (loaded dynamically from localStorage or optional config file)
let clientId = null;
let redirectUri = null;
let useImplicit = true;
const scopes = [
  "user-read-playback-state",
  "user-modify-playback-state",
  "user-read-currently-playing",
  "user-library-read",
  "user-read-recently-played",
  "user-top-read",
  "playlist-read-private",
  "playlist-read-collaborative",
  "user-read-email",
  "user-read-private"
];

// DJ Session Management
let currentDjSession = null;

async function loadConfig() {
  try {
    const localCfg = JSON.parse(localStorage.getItem('spotify_config') || '{}');
    clientId = localCfg.clientId || clientId;
    redirectUri = localCfg.redirectUri || redirectUri;
    useImplicit = (typeof localCfg.useImplicit === 'boolean') ? localCfg.useImplicit : true;
  } catch {}
  if (!clientId || !redirectUri) {
    try {
      const res = await fetch('spotify.config.json', { cache: 'no-store' });
      if (res.ok) {
        const json = await res.json();
        clientId = json.clientId || clientId;
        redirectUri = json.redirectUri || redirectUri;
        if (typeof json.useImplicit === 'boolean') useImplicit = json.useImplicit;
      }
    } catch {}
  }
}

function generateRandomString(length) {
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  return Array.from(array, dec => ('0' + dec.toString(16)).slice(-2)).join('');
}

async function sha256(plain) {
  const encoder = new TextEncoder();
  const data = encoder.encode(plain);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

async function loginWithSpotify() {
  await loadConfig();
  if (!clientId || !redirectUri) {
    alert('Please configure your Spotify Client ID and Redirect URI (gear icon).');
    openConfig();
    return;
  }
  const authEndpoint = 'https://accounts.spotify.com/authorize';
  const state = generateRandomString(16);
  localStorage.setItem('sp_auth_state', state);
  if (useImplicit) {
    const params = new URLSearchParams({
      client_id: clientId,
      response_type: 'token',
      redirect_uri: redirectUri,
      scope: scopes.join(' '),
      show_dialog: 'true',
      state
    });
    window.location.assign(`${authEndpoint}?${params.toString()}`);
  } else {
    const codeVerifier = generateRandomString(64);
    const codeChallenge = await sha256(codeVerifier);
    localStorage.setItem('sp_code_verifier', codeVerifier);
    const params = new URLSearchParams({
      client_id: clientId,
      response_type: 'code',
      redirect_uri: redirectUri,
      scope: scopes.join(' '),
      code_challenge_method: 'S256',
      code_challenge: codeChallenge,
      show_dialog: 'true',
      state
    });
    window.location.assign(`${authEndpoint}?${params.toString()}`);
  }
}

// DJ Session Functions
async function startDjSession(mode, genre, artists = [], batchSize = 150) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/spotify/dj/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        mode: mode,
        genre: genre,
        artists: artists,
        batch_size: batchSize,
        strict_primary: true
      })
    });

    if (response.ok) {
      const result = await response.json();
      if (result.ok) {
        currentDjSession = result;
        updateDjSessionDisplay(result);
        showNotification(`🎵 DJ Session started! ${result.hint}`, 'success');
      } else {
        showNotification(`❌ DJ Session failed: ${result.error}`, 'error');
      }
    } else {
      showNotification('❌ Failed to start DJ session', 'error');
    }
  } catch (error) {
    console.error('DJ session error:', error);
    showNotification('❌ Network error starting DJ session', 'error');
  }
}

function updateDjSessionDisplay(session) {
  const djDisplay = document.getElementById('djSessionDisplay') || createDjSessionDisplay();
  
  djDisplay.innerHTML = `
    <h3>🎵 Current DJ Session</h3>
    <p><strong>Mode:</strong> ${session.mode}</p>
    <p><strong>Genre:</strong> ${session.genre}</p>
    <p><strong>Artists:</strong> ${session.artists.join(', ') || 'Random'}</p>
    <p><strong>Tracks:</strong> ${session.batch}</p>
    <p><strong>Status:</strong> Started: ${session.started}, Queued: ${session.queued}</p>
    <button onclick="stopDjSession()" class="stop-dj-btn">Stop Session</button>
  `;
}

function createDjSessionDisplay() {
  const display = document.createElement('div');
  display.id = 'djSessionDisplay';
  display.style.cssText = `
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
    font-family: 'Arial', sans-serif;
  `;
  
  const profileSection = document.querySelector('.profile-section');
  if (profileSection) {
    profileSection.appendChild(display);
  }
  
  return display;
}

function stopDjSession() {
  currentDjSession = null;
  const djDisplay = document.getElementById('djSessionDisplay');
  if (djDisplay) {
    djDisplay.remove();
  }
  showNotification('🛑 DJ Session stopped', 'info');
}

function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    border-radius: 5px;
    color: white;
    font-weight: bold;
    z-index: 10000;
    animation: slideIn 0.3s ease-out;
  `;
  
  // Set background color based on type
  switch (type) {
    case 'success':
      notification.style.backgroundColor = '#4CAF50';
      break;
    case 'error':
      notification.style.backgroundColor = '#F44336';
      break;
    case 'warning':
      notification.style.backgroundColor = '#FF9800';
      break;
    default:
      notification.style.backgroundColor = '#2196F3';
  }
  
  notification.textContent = message;
  document.body.appendChild(notification);
  
  // Remove after 3 seconds
  setTimeout(() => {
    notification.remove();
  }, 3000);
}

// Add DJ controls to the profile page
function addDjControls() {
  const profileSection = document.querySelector('.container');
  if (!profileSection) return;
  
  const djControls = document.createElement('div');
  djControls.className = 'dj-controls';
  djControls.innerHTML = `
    <h3>🎵 DJ Controls</h3>
    <div style="margin: 15px 0;">
      <label>Mode:</label>
      <select id="djMode">
        <option value="random">Random</option>
        <option value="artist">Artist</option>
      </select>
    </div>
    <div style="margin: 15px 0;">
      <label>Genre:</label>
      <select id="djGenre">
        <option value="Remix">Remix</option>
        <option value="LOFI">LOFI</option>
        <option value="Mashup">Mashup</option>
      </select>
    </div>
    <div style="margin: 15px 0;">
      <label>Artists (comma-separated):</label>
      <input type="text" id="djArtists" placeholder="Artist 1, Artist 2">
    </div>
    <div style="margin: 15px 0;">
      <label>Batch Size:</label>
      <input type="number" id="djBatchSize" value="150" min="10" max="500">
    </div>
    <button onclick="startDjFromControls()">Start DJ Session</button>
    <button onclick="stopDjSession()" class="stop">Stop Session</button>
  `;
  
  profileSection.appendChild(djControls);
}

function startDjFromControls() {
  const mode = document.getElementById('djMode').value;
  const genre = document.getElementById('djGenre').value;
  const artistsText = document.getElementById('djArtists').value;
  const batchSize = parseInt(document.getElementById('djBatchSize').value);
  
  const artists = artistsText ? artistsText.split(',').map(a => a.trim()).filter(a => a) : [];
  
  if (mode === 'artist' && artists.length === 0) {
    showNotification('❌ Please enter at least one artist for artist mode', 'warning');
    return;
  }
  
  startDjSession(mode, genre, artists, batchSize);
}

// Back button
function goBack() {
  window.history.back();
}

// Info Modal Controls
function openInfo() {
  document.getElementById('infoModal').style.display = 'block';
}

function closeInfo() {
  document.getElementById('infoModal').style.display = 'none';
}

// Config modal controls
function openConfig() {
  document.getElementById('configModal').style.display = 'block';
  const saved = JSON.parse(localStorage.getItem('spotify_config') || '{}');
  document.getElementById('cfgClientId').value = saved.clientId || '';
  document.getElementById('cfgRedirectUri').value = saved.redirectUri || window.location.href;
  document.getElementById('cfgUseImplicit').checked = (typeof saved.useImplicit === 'boolean') ? saved.useImplicit : true;
}

function closeConfig() {
  document.getElementById('configModal').style.display = 'none';
}

function saveConfig() {
  const cfg = {
    clientId: document.getElementById('cfgClientId').value.trim(),
    redirectUri: document.getElementById('cfgRedirectUri').value.trim(),
    useImplicit: document.getElementById('cfgUseImplicit').checked
  };
  localStorage.setItem('spotify_config', JSON.stringify(cfg));
  clientId = cfg.clientId;
  redirectUri = cfg.redirectUri;
  useImplicit = cfg.useImplicit;
  closeConfig();
}

// Token handling (Authorization Code with PKCE requires a backend exchange)
// For a pure static frontend, we fall back to Implicit Grant when no backend is present.
async function tryHandleRedirect() {
  await loadConfig();
  const url = new URL(window.location.href);
  const hash = url.hash.startsWith('#') ? new URLSearchParams(url.hash.slice(1)) : null;
  const query = url.search ? new URLSearchParams(url.search) : null;

  // Implicit grant flow token in URL fragment
  if (hash && hash.get('access_token')) {
    const returnedState = hash.get('state');
    const storedState = localStorage.getItem('sp_auth_state');
    if (storedState && returnedState !== storedState) {
      document.getElementById('auth-status').innerText = 'State mismatch. Aborting for security.';
      return;
    }
    localStorage.removeItem('sp_auth_state');
    const token = hash.get('access_token');
    const expiresIn = parseInt(hash.get('expires_in') || '3600', 10);
    const expiryTs = Date.now() + (expiresIn * 1000);
    localStorage.setItem('sp_access_token', token);
    localStorage.setItem('sp_access_expiry', String(expiryTs));
    history.replaceState({}, document.title, url.pathname);
    renderAuthState();
    return;
  }

  // If we returned with an authorization code but have no backend, guide the user
  if (query && query.get('code')) {
    const returnedState = query.get('state');
    const storedState = localStorage.getItem('sp_auth_state');
    if (storedState && returnedState !== storedState) {
      document.getElementById('auth-status').innerText = 'State mismatch. Aborting for security.';
      return;
    }
    localStorage.removeItem('sp_auth_state');
    document.getElementById('auth-status').innerText = 'Authorization code received. A backend endpoint is required to exchange code for tokens (per Spotify PKCE).';
  }
}

function getStoredAccessToken() {
  const token = localStorage.getItem('sp_access_token');
  const expiry = parseInt(localStorage.getItem('sp_access_expiry') || '0', 10);
  if (token && Date.now() < expiry) return token;
  return null;
}

function disconnectSpotify() {
  localStorage.removeItem('sp_access_token');
  localStorage.removeItem('sp_access_expiry');
  renderAuthState();
}

async function fetchSpotify(endpoint, options = {}) {
  const token = getStoredAccessToken();
  if (!token) throw new Error('Not authenticated');
  const res = await fetch(`https://api.spotify.com/v1/${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  });
  if (res.status === 401) {
    // token expired
    disconnectSpotify();
    throw new Error('Token expired');
  }
  return res.json();
}

async function renderAuthState() {
  const status = document.getElementById('auth-status');
  const userInfo = document.getElementById('user-info');
  const disconnectBtn = document.getElementById('disconnectBtn');
  userInfo.textContent = '';
  const token = getStoredAccessToken();
  if (!token) {
    status.textContent = 'Not connected.';
    disconnectBtn.style.display = 'none';
    return;
  }
  status.textContent = 'Connected to Spotify.';
  disconnectBtn.style.display = 'inline-flex';
  try {
    const me = await fetchSpotify('me');
    userInfo.innerHTML = `Logged in as <strong>${me.display_name || me.id}</strong>`;
    // Fetch recent listening history
    const recent = await fetchSpotify('me/player/recently-played?limit=10');
    const items = recent.items || [];
    if (items.length) {
      const list = document.createElement('ul');
      list.style.listStyle = 'none';
      list.style.padding = '0';
      items.forEach((it) => {
        const li = document.createElement('li');
        const track = it.track;
        li.textContent = `${track.name} — ${track.artists.map(a => a.name).join(', ')}`;
        list.appendChild(li);
      });
      const wrapper = document.createElement('div');
      wrapper.style.marginTop = '10px';
      const title = document.createElement('div');
      title.style.marginBottom = '6px';
      title.style.opacity = '0.9';
      title.textContent = 'Recently Played:';
      wrapper.appendChild(title);
      wrapper.appendChild(list);
      userInfo.appendChild(wrapper);
    }
  } catch (e) {
    status.textContent = `Connected, but failed to fetch profile: ${e.message}`;
  }
}

// On load
(async function init() {
  await tryHandleRedirect();
  await renderAuthState();
  
  // Add DJ controls after a short delay to ensure DOM is ready
  setTimeout(addDjControls, 1000);
})();
