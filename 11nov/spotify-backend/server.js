import express from 'express';
import session from 'express-session';
import cors from 'cors';
import fetch from 'node-fetch';
import dotenv from 'dotenv';
import https from 'https';
import fs from 'fs';

dotenv.config();

const {
  SPOTIFY_CLIENT_ID,
  SPOTIFY_CLIENT_SECRET,
  SPOTIFY_REDIRECT_URI = 'http://localhost:3000/auth/callback',
  FRONTEND_ORIGIN = 'http://127.0.0.1:5500',
  SESSION_SECRET = 'dev',
  PORT = 3000,
  HTTPS = '0',
  TLS_KEY_PATH = './certs/key.pem',
  TLS_CERT_PATH = './certs/cert.pem'
} = process.env;

const app = express();
const allowedOrigins = [FRONTEND_ORIGIN, 'http://127.0.0.1:5500', 'http://localhost:5500'];
app.use(cors({
  origin: function(origin, callback){
    // allow non-browser (no origin) and explicit allowed origins
    if (!origin || allowedOrigins.includes(origin)) return callback(null, true);
    return callback(new Error('Not allowed by CORS'));
  },
  credentials: true
}));
app.options('*', cors({ origin: allowedOrigins, credentials: true }));
app.use(express.json());
app.use(session({
  secret: SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: { sameSite: 'lax', secure: false }
}));

const SP_AUTH = {
  token: 'https://accounts.spotify.com/api/token',
  auth: 'https://accounts.spotify.com/authorize',
  api: 'https://api.spotify.com/v1'
};

const SCOPES = [
  'user-read-playback-state',
  'user-modify-playback-state',
  'user-read-currently-playing',
  'playlist-read-private',
  'user-read-email',
  'user-read-private'
].join(' ');

function ensureAuth(req, res, next) {
  if (!req.session.spotify || !req.session.spotify.access_token) {
    return res.status(401).json({ ok: false, error: 'NOT_AUTHENTICATED' });
  }
  next();
}

async function refreshToken(req) {
  if (!req.session.spotify?.refresh_token) return false;
  const params = new URLSearchParams();
  params.set('grant_type', 'refresh_token');
  params.set('refresh_token', req.session.spotify.refresh_token);
  const b64 = Buffer.from(`${SPOTIFY_CLIENT_ID}:${SPOTIFY_CLIENT_SECRET}`).toString('base64');
  const r = await fetch(SP_AUTH.token, {
    method: 'POST',
    headers: { Authorization: `Basic ${b64}`, 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString()
  });
  if (!r.ok) return false;
  const json = await r.json();
  req.session.spotify.access_token = json.access_token;
  if (json.refresh_token) req.session.spotify.refresh_token = json.refresh_token;
  return true;
}

async function spFetch(req, path, opts = {}) {
  const doFetch = async () => fetch(`${SP_AUTH.api}/${path}`, {
    ...opts,
    headers: {
      ...(opts.headers || {}),
      Authorization: `Bearer ${req.session.spotify.access_token}`,
      'Content-Type': 'application/json'
    }
  });
  let res = await doFetch();
  if (res.status === 401) {
    const ok = await refreshToken(req);
    if (!ok) return res;
    res = await doFetch();
  }
  return res;
}

app.get('/auth/login', (req, res) => {
  const params = new URLSearchParams({
    client_id: SPOTIFY_CLIENT_ID,
    response_type: 'code',
    redirect_uri: SPOTIFY_REDIRECT_URI,
    scope: SCOPES,
    show_dialog: 'true',
    state: Math.random().toString(36).slice(2)
  });
  res.redirect(`${SP_AUTH.auth}?${params.toString()}`);
});

app.get('/auth/callback', async (req, res) => {
  const { code, error } = req.query;
  if (error || !code) return res.status(400).send('Spotify auth failed.');
  const params = new URLSearchParams();
  params.set('grant_type', 'authorization_code');
  params.set('code', code);
  params.set('redirect_uri', SPOTIFY_REDIRECT_URI);
  const b64 = Buffer.from(`${SPOTIFY_CLIENT_ID}:${SPOTIFY_CLIENT_SECRET}`).toString('base64');
  const tokenRes = await fetch(SP_AUTH.token, {
    method: 'POST',
    headers: { Authorization: `Basic ${b64}`, 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString()
  });
  if (!tokenRes.ok) return res.status(500).send('Token exchange failed.');
  const tokens = await tokenRes.json();
  req.session.spotify = { access_token: tokens.access_token, refresh_token: tokens.refresh_token };
  res.redirect(`${FRONTEND_ORIGIN}/profile.html`);
});

app.get('/api/spotify/status', async (req, res) => {
  if (!req.session.spotify?.access_token) return res.json({ authenticated: false });
  const meRes = await spFetch(req, 'me');
  if (!meRes.ok) return res.json({ authenticated: true });
  const me = await meRes.json();
  res.json({ authenticated: true, user: { id: me.id, name: me.display_name } });
});

app.get('/api/spotify/current', ensureAuth, async (req, res) => {
  const r = await spFetch(req, 'me/player/currently-playing');
  if (r.status === 204) return res.json({ playing: false });
  const json = await r.json().catch(() => ({}));
  res.json(json);
});

app.post('/api/spotify/control', ensureAuth, async (req, res) => {
  const { action, delta, device_id } = req.body || {};
  try {
    if (action === 'play') {
      const r = await spFetch(req, `me/player/play${device_id ? `?device_id=${device_id}` : ''}`, { method: 'PUT' });
      return res.status(r.status).json({ ok: r.ok });
    }
    if (action === 'pause') {
      const r = await spFetch(req, 'me/player/pause', { method: 'PUT' });
      return res.status(r.status).json({ ok: r.ok });
    }
    if (action === 'next') {
      const r = await spFetch(req, 'me/player/next', { method: 'POST' });
      return res.status(r.status).json({ ok: r.ok });
    }
    if (action === 'previous') {
      const r = await spFetch(req, 'me/player/previous', { method: 'POST' });
      return res.status(r.status).json({ ok: r.ok });
    }
    if (action === 'seek') {
      const pos = Math.max(0, parseInt(delta || 0, 10));
      const r = await spFetch(req, `me/player/seek?position_ms=${pos}`, { method: 'PUT' });
      return res.status(r.status).json({ ok: r.ok });
    }
    if (action === 'volume') {
      const vol = Math.min(100, Math.max(0, parseInt(delta || 50, 10)));
      const r = await spFetch(req, `me/player/volume?volume_percent=${vol}`, { method: 'PUT' });
      return res.status(r.status).json({ ok: r.ok });
    }
    return res.status(400).json({ ok: false, error: 'UNKNOWN_ACTION' });
  } catch (e) {
    return res.status(500).json({ ok: false, error: 'CONTROL_FAILED' });
  }
});

app.post('/api/spotify/play', ensureAuth, async (req, res) => {
  const { query, uri, device_id } = req.body || {};
  try {
    if (query) {
      const q = new URLSearchParams({ q: query, type: 'track', limit: '1' });
      const search = await spFetch(req, `search?${q.toString()}`);
      const data = await search.json();
      const track = data.tracks?.items?.[0];
      if (!track?.uri) return res.status(404).json({ ok: false, error: 'NO_MATCH' });
      const r = await spFetch(req, `me/player/play${device_id ? `?device_id=${device_id}` : ''}`, {
        method: 'PUT', body: JSON.stringify({ uris: [track.uri] })
      });
      return res.status(r.status).json({ ok: r.ok });
    }
    if (uri) {
      const r = await spFetch(req, `me/player/play${device_id ? `?device_id=${device_id}` : ''}`, {
        method: 'PUT', body: JSON.stringify({ uris: [uri] })
      });
      return res.status(r.status).json({ ok: r.ok });
    }
    return res.status(400).json({ ok: false, error: 'MISSING_QUERY_OR_URI' });
  } catch (e) {
    return res.status(500).json({ ok: false, error: 'PLAY_FAILED' });
  }
});

app.get('/api/spotify/devices', ensureAuth, async (req, res) => {
  const r = await spFetch(req, 'me/player/devices');
  const j = await r.json();
  res.json(j);
});

if (HTTPS === '1') {
  try {
    const key = fs.readFileSync(TLS_KEY_PATH);
    const cert = fs.readFileSync(TLS_CERT_PATH);
    https.createServer({ key, cert }, app).listen(PORT, () => {
      console.log(`Spotify backend running (HTTPS) on https://localhost:${PORT}`);
    });
  } catch (e) {
    console.error('Failed to start HTTPS server. Check TLS_KEY_PATH/TLS_CERT_PATH.', e.message);
    process.exit(1);
  }
} else {
  app.listen(PORT, () => {
    console.log(`Spotify backend running on http://localhost:${PORT}`);
  });
}


