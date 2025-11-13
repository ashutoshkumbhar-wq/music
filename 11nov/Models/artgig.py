# dj_queue_20_after_10_dedupe_tags_menu.py
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

# Default (will be overwritten by menu)
TAGS: List[str] = []

# Predefined tag packs
TAG_PROFILES: Dict[str, List[str]] = {
    "1": ["remix","bootleg","rework","vip","festival mix","club mix","extended mix","edit","mix"],
    "2": ["mashup","blend","bootleg mashup","megamix","transition mix","multi-track mix","dj mix","live mashup"],
    "3": ["lofi","chillhop","study beats","jazzy lofi","ambient lofi","relax beats","sleep lofi","aesthetic lofi"],
    "4": ["slowed","reverb","slowed + reverb","slowed edit","chopped and screwed","deep reverb","dreamy slowed"],
}

EXCLUDE_WORDS = re.compile(r"(?i)\b(cover|karaoke)\b")

MAX_PAGES_ARTIST = 5
MAX_PAGES_RANDOM = 5
API_SLEEP = 0.10

INITIAL_BATCH     = 50
CHANGES_PER_TOPUP = 10
TOPUP_BATCH       = 20
POLL_SECS         = 2.0

# ====== Auth ======
def spotify_client() -> spotipy.Spotify:
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES,
            open_browser=True,
            cache_path=CACHE_PATH,
        )
    )

def ensure_active_device(sp: spotipy.Spotify) -> Optional[str]:
    devices = sp.devices().get("devices", [])
    if not devices: return None
    for d in devices:
        if d.get("is_active"): return d.get("id")
    target = devices[0]
    sp.transfer_playback(device_id=target["id"], force_play=True)
    time.sleep(0.4)
    return target["id"]

# ====== Tag selection menu ======
def choose_tags_menu() -> List[str]:
    print("\n=== Select Tag Type ===")
    print("1) Remix / Edits (remix, vip, club mix, extended mix...)")
    print("2) Mashup (mashup, blend, megamix, transition mix...)")
    print("3) Lofi (lofi, chillhop, study beats, ambient lofi...)")
    print("4) Slowed + Reverb (slowed, slowed + reverb, chopped & screwed...)")

    sel = input("Choose 1, 2, 3, or 4: ").strip()
    if sel not in TAG_PROFILES:
        print("❌ Invalid choice — defaulting to Remix / Edits.")
        sel = "1"
    return TAG_PROFILES[sel]

# ====== Dedup key ======
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

# ====== Helpers ======
def keep_track(t: dict, tag_rx: re.Pattern, seen_uris: Set[str], seen_keys: Set[str]) -> Optional[str]:
    name = t.get("name") or ""
    if EXCLUDE_WORDS.search(name):
        return None
    album = (t.get("album") or {}).get("name") or ""
    if not (tag_rx.search(name) or tag_rx.search(album)):
        return None
    uri = t.get("uri")
    if not uri or uri in seen_uris:
        return None
    key = song_key(t)
    if key in seen_keys:
        return None
    seen_uris.add(uri)
    seen_keys.add(key)
    return uri

def sp_search_safe(sp, **kwargs):
    tries = 0
    while True:
        try:
            return sp.search(**kwargs)
        except (ReadTimeout, ReqConnErr, SpotifyException):
            tries += 1
            time.sleep(min(2.0, 0.25 * (2 ** tries)))
            if tries >= 5: raise

# ====== Artist / Random ======
def _artist_gen(sp, artist_name: str, tag_rx: re.Pattern, seen_uris: Set[str], seen_keys: Set[str], tags: List[str]) -> Iterable[str]:
    for tag in tags:
        for page in range(MAX_PAGES_ARTIST):
            try:
                res = sp_search_safe(sp,
                    q=f'artist:"{artist_name}" {tag}',
                    type="track", limit=50, offset=page*50, market=MARKET)
            except Exception:
                continue
            items = res.get("tracks", {}).get("items", []) or []
            if not items: break
            random.shuffle(items)
            for t in items:
                uri = keep_track(t, tag_rx, seen_uris, seen_keys)
                if uri: yield uri
            time.sleep(API_SLEEP)

def search_by_artists(sp, artists: List[str], max_tracks: int,
                      seen_uris: Set[str], seen_keys: Set[str], tags: List[str]) -> List[str]:
    tag_rx = re.compile(r"(?i)\b(" + "|".join(re.escape(t) for t in tags) + r")\b")
    gens = {a: _artist_gen(sp, a, tag_rx, seen_uris, seen_keys, tags) for a in artists}
    out, order = [], list(gens.keys())

    while order and (max_tracks <= 0 or len(out) < max_tracks):
        for a in list(order):
            if max_tracks > 0 and len(out) >= max_tracks: break
            try:
                uri = next(gens[a])
                out.append(uri)
            except StopIteration:
                order.remove(a)
    return out[:max_tracks]

def search_random(sp, max_tracks: int,
                  seen_uris: Set[str], seen_keys: Set[str], tags: List[str]) -> List[str]:
    uris = []
    tag_rx = re.compile(r"(?i)\b(" + "|".join(re.escape(t) for t in tags) + r")\b")
    for tag in tags:
        for page in range(MAX_PAGES_RANDOM):
            try:
                res = sp_search_safe(sp,
                    q=tag, type="track", limit=50, offset=page*50, market=MARKET)
            except Exception:
                continue
            items = res.get("tracks", {}).get("items", []) or []
            if not items: break
            random.shuffle(items)
            for t in items:
                uri = keep_track(t, tag_rx, seen_uris, seen_keys)
                if uri:
                    uris.append(uri)
                    if 0 < max_tracks <= len(uris): return uris
            time.sleep(API_SLEEP)
    return uris[:max_tracks]

# ====== Queue ======
def start_and_queue(sp, device_id: str, uris: List[str]) -> None:
    if not uris: return
    sp.start_playback(device_id=device_id, uris=[uris[0]])
    for u in uris[1:]:
        try:
            sp.add_to_queue(u, device_id=device_id); time.sleep(API_SLEEP)
        except SpotifyException:
            break
    print(f"▶ Started playback + queued {len(uris)-1} tracks.")

# ====== Pump Loop ======
def pump_loop(sp, device_id: str, mode: str, artists: List[str], tags: List[str]):
    managed_uris, managed_keys = set(), set()
    last_uri, change_count = None, 0

    def fetch(n: int) -> List[str]:
        if mode == "artist":
            return search_by_artists(sp, artists, n, managed_uris, managed_keys, tags)
        return search_random(sp, n, managed_uris, managed_keys, tags)

    seed = fetch(INITIAL_BATCH)
    random.shuffle(seed)
    start_and_queue(sp, device_id, seed)
    managed_uris.update(seed)

    print(f"🔁 Rule: after 10 changes → add 20 (with dedupe). Active tags: {', '.join(tags)}")

    while True:
        time.sleep(POLL_SECS)
        try:
            pb = sp.current_playback()
        except Exception:
            continue
        cur_uri = ((pb or {}).get("item") or {}).get("uri")

        if cur_uri and last_uri and cur_uri != last_uri:
            change_count += 1
            if change_count >= CHANGES_PER_TOPUP:
                more = fetch(TOPUP_BATCH)
                random.shuffle(more)
                added = 0
                for u in more:
                    try:
                        sp.add_to_queue(u, device_id=device_id)
                        managed_uris.add(u)
                        added += 1
                        time.sleep(API_SLEEP)
                    except SpotifyException:
                        break
                print(f"✅ {CHANGES_PER_TOPUP} changes → added {added} tracks.")
                change_count = 0
        last_uri = cur_uri

# ====== Main ======
def main():
    sp = spotify_client()
    tags = choose_tags_menu()
    print("=== DJ Queue (20-after-10, De-duplicated) ===")
    print("1) Artist mode")
    print("2) Random mode")
    mode = input("Choose 1 or 2: ").strip()

    if mode == "1":
        artists = [a.strip() for a in input("Enter artist names (comma-separated): ").split(",") if a.strip()]
        if not artists:
            print("❌ No artists entered.")
            sys.exit(0)
        selected_mode = "artist"
    else:
        artists, selected_mode = [], "random"

    device_id = ensure_active_device(sp)
    if not device_id:
        print("❌ No active Spotify device.")
        sys.exit(1)

    try:
        pump_loop(sp, device_id, selected_mode, artists, tags)
    except KeyboardInterrupt:
        print("\nExiting…")

if __name__ == "__main__":
    main()