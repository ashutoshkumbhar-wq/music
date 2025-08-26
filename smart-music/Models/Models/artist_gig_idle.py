# dj_queue_500_once.py
# pip install spotipy

import os, sys, time, re, random
from typing import List, Optional, Set, Iterable, Dict
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from requests.exceptions import ReadTimeout, ConnectionError as ReqConnErr

# ====== CREDENTIALS ======
CLIENT_ID     = os.getenv("SPOTIPY_CLIENT_ID",     "0c91f9e84c8648188f943938a28ae765")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "3b9bdccd604c402c8833b80daf1b87ed")
REDIRECT_URI  = os.getenv("SPOTIPY_REDIRECT_URI",  "http://127.0.0.1:8888/callback")

# ====== CONFIG ======
MARKET = "IN"
SCOPES = "user-modify-playback-state user-read-playback-state"
CACHE_PATH = ".cache-dj-session"

TAGS = ["remix","bootleg","rework","vip","festival mix","club mix","extended mix","edit","mix"]
EXCLUDE_WORDS = re.compile(r"(?i)\b(cover|karaoke)\b")

MAX_PAGES_ARTIST = 5
MAX_PAGES_RANDOM = 5
API_SLEEP = 0.10

# changed: initial batch 500, no refill
INITIAL_BATCH = 150

STRICT_PRIMARY = True

def spotify_client() -> spotipy.Spotify:
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES,
            open_browser=True,
            cache_path=CACHE_PATH,
        ),
        requests_timeout=20,
        retries=8,
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

# === same dedupe helpers ===
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

def sp_search_safe(sp, **kwargs):
    while True:
        try:
            return sp.search(**kwargs)
        except (ReadTimeout, ReqConnErr, SpotifyException):
            time.sleep(0.5)

def keep_track(t, tag_rx, seen_uris, seen_keys):
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

def resolve_artist_ids(sp, names: List[str]) -> Dict[str,str]:
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

def _artist_gen(sp, artist_name, allowed_ids, tag_rx, seen_uris, seen_keys):
    for tag in TAGS:
        for page in range(MAX_PAGES_ARTIST):
            res = sp_search_safe(sp,
                q=f'artist:"{artist_name}" {tag}',
                type="track", limit=50, offset=page*50, market=MARKET)
            items = res.get("tracks", {}).get("items") or []
            if not items: break
            random.shuffle(items)
            for t in items:
                if not is_allowed_artist(t, allowed_ids, STRICT_PRIMARY): continue
                uri = keep_track(t, tag_rx, seen_uris, seen_keys)
                if uri: yield uri
            time.sleep(API_SLEEP)

def search_by_artists(sp, artists, max_tracks, seen_uris, seen_keys):
    name_to_id = resolve_artist_ids(sp, artists)
    allowed_ids = {aid for aid in name_to_id.values() if aid}
    tag_rx = re.compile(r"(?i)\b(" + "|".join(re.escape(t) for t in TAGS) + r")\b")
    gens = {a: _artist_gen(sp, a, allowed_ids, tag_rx, seen_uris, seen_keys) for a in artists}
    order = list(gens.keys())
    out = []
    while order and (max_tracks <= 0 or len(out) < max_tracks):
        for a in list(order):
            if max_tracks > 0 and len(out) >= max_tracks: break
            g = gens[a]
            try: out.append(next(g))
            except StopIteration: order.remove(a); gens.pop(a,None)
    return out if max_tracks<=0 else out[:max_tracks]

def search_random(sp, max_tracks, seen_uris, seen_keys):
    uris = []
    tag_rx = re.compile(r"(?i)\b(" + "|".join(re.escape(t) for t in TAGS) + r")\b")
    for tag in TAGS:
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
    return uris if max_tracks<=0 else uris[:max_tracks]

def start_and_queue(sp, device_id, uris):
    if not uris: return
    sp.start_playback(device_id=device_id, uris=[uris[0]])
    for u in uris[1:]:
        try: sp.add_to_queue(u, device_id=device_id); time.sleep(API_SLEEP)
        except SpotifyException: break
    print(f"▶️ Queued {len(uris)} tracks.")

# ====== Main ======
def main():
    sp = spotify_client()
    print("=== DJ Queue (One-shot, 500 Tracks, De-duplicated) ===")
    print("1) Artist mode")
    print("2) Random mode")
    mode = input("Choose 1 or 2: ").strip()
    if mode == "1":
        artists = [a.strip() for a in input("Enter artist names (comma-separated): ").split(",") if a.strip()]
        if not artists: print("❌ No artists entered."); sys.exit(0)
        selected_mode = "artist"
    else:
        artists, selected_mode = [], "random"

    device_id = ensure_active_device(sp)
    if not device_id: print("❌ No active Spotify device."); sys.exit(1)

    seen_uris, seen_keys = set(), set()
    if selected_mode=="artist":
        tracks = search_by_artists(sp, artists, INITIAL_BATCH, seen_uris, seen_keys)
    else:
        tracks = search_random(sp, INITIAL_BATCH, seen_uris, seen_keys)

    random.shuffle(tracks)
    start_and_queue(sp, device_id, tracks)

if __name__ == "__main__":
    main()
