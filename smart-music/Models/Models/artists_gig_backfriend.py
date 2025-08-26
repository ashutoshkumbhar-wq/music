# dj_queue_once_service.py
# pip install spotipy flask flask-cors
import os, time, re, random
from typing import List, Optional, Set, Iterable, Dict, Any
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from requests.exceptions import ReadTimeout, ConnectionError as ReqConnErr

# ====== CREDENTIALS ======
CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID",     os.getenv("SPOTIPY_CLIENT_ID",     "0c91f9e84c8648188f943938a28ae765"))
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", os.getenv("SPOTIPY_CLIENT_SECRET", "3b9bdccd604c402c8833b80daf1b87ed"))
REDIRECT_URI  = os.getenv("SPOTIFY_REDIRECT_URI",  os.getenv("SPOTIPY_REDIRECT_URI",  "http://127.0.0.1:8888/callback"))
CACHE_PATH    = os.getenv("SPOTIFY_CACHE_PATH",    ".cache-dj-session")

# ====== CONFIG ======
MARKET = os.getenv("SPOTIFY_MARKET", "IN")
SCOPES = "user-modify-playback-state user-read-playback-state"
API_SLEEP = 0.10
MAX_PAGES_ARTIST = 5
MAX_PAGES_RANDOM = 5

# Default: one-shot batch size (you can override per call)
INITIAL_BATCH = int(os.getenv("DJ_ONCE_BATCH", "150"))

# Strict primary-artist filter (track's primary artist must match)
STRICT_PRIMARY = os.getenv("DJ_STRICT_PRIMARY", "1") == "1"

# ====== GENRE TAGS (your 3) ======
GENRE_TAGS: Dict[str, List[str]] = {
    "Remix":  ["remix","bootleg","rework","vip","festival mix","club mix","extended mix","edit","mix"],
    "LOFI":   ["lofi","chill","study","sleep","late night","ambient","beats"],
    "Mashup": ["mashup","blend","mix","bootleg mashup","dj mashup","party mashup"],
}
EXCLUDE_WORDS = re.compile(r"(?i)\b(cover|karaoke)\b")

# === dedupe helpers (same idea as your base) ===
REMSTRIP_RX = re.compile(r"(?i)\s*-\s*(remaster(?:ed)?(?: \d{4})?|mono version|deluxe version|expanded edition)\b.*")
FEAT_RX     = re.compile(r"(?i)\s*\(feat\.[^)]+\)")

def song_key(track: dict) -> str:
    title = (track.get("name") or "").strip()
    title = FEAT_RX.sub("", title)
    title = REMSTRIP_RX.sub("", title)
    title = re.sub(r"\s+", " ", title).lower()
    artists = track.get("artists") or []
    primary = (artists[0].get("name") if artists else "").strip().lower()
    return f"{title}||{primary}"

def _tag_rx(tags: List[str]) -> re.Pattern:
    return re.compile(r"(?i)\b(" + "|".join(re.escape(t) for t in tags) + r")\b")

# ====== Spotify auth / device ======
def spotify_client() -> spotipy.Spotify:
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI, scope=SCOPES,
            open_browser=False, cache_path=CACHE_PATH,
        ),
        requests_timeout=20, retries=8,
    )

def ensure_active_device(sp: spotipy.Spotify) -> Optional[str]:
    devices = sp.devices().get("devices", [])
    if not devices: return None
    for d in devices:
        if d.get("is_active"): return d.get("id")
    target = devices[0]
    sp.transfer_playback(device_id=target["id"], force_play=True)
    time.sleep(0.3)
    return target["id"]

# ====== Helpers ======
def sp_search_safe(sp, **kwargs):
    while True:
        try:
            return sp.search(**kwargs)
        except (ReadTimeout, ReqConnErr, SpotifyException):
            time.sleep(0.5)

def keep_track(t: dict, tag_rx: re.Pattern, seen_uris: Set[str], seen_keys: Set[str]) -> Optional[str]:
    name = t.get("name") or ""
    if EXCLUDE_WORDS.search(name): return None
    album = (t.get("album") or {}).get("name") or ""
    if not (tag_rx.search(name) or tag_rx.search(album)): return None
    uri = t.get("uri")
    if not uri or uri in seen_uris: return None
    key = song_key(t)
    if key in seen_keys: return None
    seen_uris.add(uri); seen_keys.add(key)
    return uri

def resolve_artist_ids(sp, names: List[str]) -> Dict[str, str]:
    out = {}
    for n in names:
        res = sp_search_safe(sp, q=f'artist:"{n}"', type="artist", limit=1, market=MARKET)
        items = res.get("artists", {}).get("items") or []
        if items: out[n] = items[0].get("id")
    return out

def is_allowed_artist(track, allowed_ids: Set[str], strict_primary=True) -> bool:
    artists = track.get("artists") or []
    if not artists: return False
    if strict_primary:
        return (artists[0].get("id") or "") in allowed_ids
    return any((a.get("id") or "") in allowed_ids for a in artists)

# ====== Search (artist / random) with genre tags ======
def _artist_gen(sp, artist_name: str, allowed_ids: Set[str], tag_rx: re.Pattern,
                seen_uris: Set[str], seen_keys: Set[str], tags: List[str]):
    for tag in tags:
        for page in range(MAX_PAGES_ARTIST):
            res = sp_search_safe(sp,
                q=f'artist:"{artist_name}" {tag}', type="track",
                limit=50, offset=page*50, market=MARKET)
            items = res.get("tracks", {}).get("items") or []
            if not items: break
            random.shuffle(items)
            for t in items:
                if not is_allowed_artist(t, allowed_ids, STRICT_PRIMARY): continue
                uri = keep_track(t, tag_rx, seen_uris, seen_keys)
                if uri: yield uri
            time.sleep(API_SLEEP)

def search_by_artists(sp, artists: List[str], max_tracks: int,
                      seen_uris: Set[str], seen_keys: Set[str], tags: List[str]) -> List[str]:
    if not artists: return []
    name_to_id = resolve_artist_ids(sp, artists)
    allowed_ids = {aid for aid in name_to_id.values() if aid}
    tag_rx = _tag_rx(tags)
    gens = {a: _artist_gen(sp, a, allowed_ids, tag_rx, seen_uris, seen_keys, tags) for a in artists}
    order = list(gens.keys())
    out: List[str] = []
    while order and (max_tracks <= 0 or len(out) < max_tracks):
        for a in list(order):
            if max_tracks > 0 and len(out) >= max_tracks: break
            g = gens[a]
            try: out.append(next(g))
            except StopIteration: order.remove(a); gens.pop(a, None)
    return out if max_tracks <= 0 else out[:max_tracks]

def search_random(sp, max_tracks: int, seen_uris: Set[str], seen_keys: Set[str], tags: List[str]) -> List[str]:
    uris: List[str] = []
    tag_rx = _tag_rx(tags)
    for tag in tags:
        for page in range(MAX_PAGES_RANDOM):
            res = sp_search_safe(sp, q=tag, type="track", limit=50, offset=page*50, market=MARKET)
            items = res.get("tracks", {}).get("items") or []
            if not items: break
            random.shuffle(items)
            for t in items:
                uri = keep_track(t, tag_rx, seen_uris, seen_keys)
                if uri: uris.append(uri)
                if 0 < max_tracks <= len(uris): return uris
            time.sleep(API_SLEEP)
    return uris if max_tracks <= 0 else uris[:max_tracks]

# ====== Queue ======
def start_and_queue(sp, device_id: str, uris: List[str]) -> Dict[str, int]:
    if not uris: return {"started": 0, "queued": 0}
    started = 0; queued = 0
    try:
        sp.start_playback(device_id=device_id, uris=[uris[0]])
        started = 1
    except SpotifyException as e:
        print("⚠️ start_playback failed:", e)
    for u in uris[1:]:
        try: sp.add_to_queue(u, device_id=device_id); queued += 1; time.sleep(API_SLEEP)
        except SpotifyException: break
    return {"started": started, "queued": queued}

# ====== PUBLIC: one-shot runner for backend ======
def run_once(mode: str, genre: str, artists: List[str], batch_size: Optional[int] = None,
             strict_primary: Optional[bool] = None) -> Dict[str, Any]:
    """
    mode: 'artist' | 'random'
    genre: 'Remix' | 'LOFI' | 'Mashup'
    artists: [] (ignored for random)
    batch_size: override INITIAL_BATCH
    strict_primary: override STRICT_PRIMARY
    """
    tags = GENRE_TAGS.get(genre, GENRE_TAGS["Remix"])
    bs = int(batch_size or INITIAL_BATCH)
    sp = spotify_client()
    device_id = ensure_active_device(sp)
    if not device_id:
        return {"ok": False, "error": "No active Spotify device"}

    global STRICT_PRIMARY
    restore_strict = STRICT_PRIMARY
    if strict_primary is not None:
        STRICT_PRIMARY = bool(strict_primary)

    seen_uris: Set[str] = set()
    seen_keys: Set[str] = set()
    if mode == "artist":
        uris = search_by_artists(sp, artists, bs, seen_uris, seen_keys, tags)
        hint = ", ".join(artists[:2]) + ("…" if len(artists) > 2 else "")
    else:
        uris = search_random(sp, bs, seen_uris, seen_keys, tags)
        hint = f"Random · {genre}"

    random.shuffle(uris)
    qres = start_and_queue(sp, device_id, uris)

    # restore global STRICT_PRIMARY if we changed it
    STRICT_PRIMARY = restore_strict

    return {
        "ok": True,
        "mode": mode,
        "genre": genre,
        "artists": artists,
        "batch": len(uris),
        "hint": hint,
        **qres
    }

# ====== OPTIONAL: Flask shim ======
if os.getenv("RUN_ONCE_FLASK", "0") == "1":
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    app = Flask(__name__)
    CORS(app)

    @app.post("/once/start")
    def http_once():
        data = request.get_json(force=True)
        res = run_once(
            mode=data.get("mode", "random"),
            genre=data.get("genre", "Remix"),
            artists=data.get("artists", []),
            batch_size=data.get("batch_size"),
            strict_primary=data.get("strict_primary"),
        )
        return jsonify(res), (200 if res.get("ok") else 400)

    # if __name__ == "__main__":
    #     app.run(port=5004, debug=True)
