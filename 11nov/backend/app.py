from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import os
import sys
import joblib
import numpy as np
import cv2
import mediapipe as mp

import base64
from PIL import Image
import io
import json
import datetime

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Import configuration
try:
    from config import Config
except ImportError:
    print("Warning: config.py not found, using default values")
    class Config:
        GESTURE_CONFIDENCE_THRESHOLD = 0.8
        GESTURE_STABLE_FRAMES = 5
        GESTURE_ACTION_COOLDOWN = 1.0
        DJ_DEFAULT_BATCH_SIZE = 150
        DJ_STRICT_PRIMARY = True

# Add the gesture models path
sys.path.append('../Gesture final')

# Import your existing modules
try:
    sys.path.append('../Models/Models')
    from artists_gig_backfriend import run_once as dj_run_once
    print("DJ module imported successfully")
except ImportError as e:
    print(f"Warning: DJ module not available: {e}")
    dj_run_once = None

# Import artgig module
try:
    sys.path.append('../Models/Models')
    from artgig import (
        spotify_client, ensure_active_device, choose_tags_menu, 
        search_by_artists, search_random, start_and_queue, pump_loop,
        TAG_PROFILES
    )
    print("Artgig module imported successfully")
except ImportError as e:
    print(f"Warning: Artgig module not available: {e}")
    spotify_client = None

app = Flask(__name__)
# Allow frontend origins including local file server and dev ports
_cors_origins = getattr(Config, 'CORS_ORIGINS', [
    'http://localhost:3000', 'http://127.0.0.1:3000',
    'http://localhost:5000', 'http://127.0.0.1:5000',
    'http://localhost:5500', 'http://127.0.0.1:5500',
    'null'
])
CORS(app, resources={r"/*": {"origins": _cors_origins}}, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    try:
        origin = request.headers.get('Origin')
        if origin and origin in _cors_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Vary'] = 'Origin'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    except Exception:
        pass
    return response

# Load gesture recognition models
MODEL_PATH = getattr(Config, 'GESTURE_MODEL_PATH', "../Gesture final/gesture_model.pkl")
SCALER_PATH = getattr(Config, 'GESTURE_SCALER_PATH', "../Gesture final/scaler.pkl")

try:
    gesture_model = joblib.load(MODEL_PATH)
    gesture_scaler = joblib.load(SCALER_PATH)
    print("Gesture models loaded successfully")
    print(f"Model classes: {list(gesture_model.classes_) if hasattr(gesture_model, 'classes_') else 'Unknown'}")
except Exception as e:
    print(f"Error loading gesture models: {e}")
    gesture_model = None
    gesture_scaler = None

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ===== Helper function for Spotify OAuth =====
def _spotify_oauth():
    client_id = getattr(Config, 'SPOTIPY_CLIENT_ID', None)
    client_secret = getattr(Config, 'SPOTIPY_CLIENT_SECRET', None)
    redirect_uri = getattr(Config, 'SPOTIPY_REDIRECT_URI', 'http://localhost:5000/callback')
    scopes = os.environ.get(
        'SPOTIFY_SCOPES',
        'user-modify-playback-state user-read-playback-state user-read-currently-playing user-library-modify'
    )
    cache_path = os.environ.get('SPOTIFY_CACHE_PATH', '.cache-dj-session')
    if not client_id or not client_secret:
        print("⚠️ Spotify credentials not configured")
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scopes,
        cache_path=cache_path,
        open_browser=False,
    )

def get_spotify_client():
    """Get authenticated Spotify client for artist mix"""
    try:
        oauth = _spotify_oauth()
        token = oauth.get_cached_token()
        if not token:
            raise Exception("Not authenticated with Spotify")
        return spotipy.Spotify(auth=token['access_token'])
    except Exception as e:
        print(f"Error getting Spotify client: {e}")
        raise

@app.route('/')
def index():
    return jsonify({
        "message": "Smart Music Backend API", 
        "status": "running",
        "version": "1.0.0",
        "features": {
            "gesture_recognition": gesture_model is not None,
            "dj_control": dj_run_once is not None,
            "spotify_integration": True,
            "artist_mix": True,
            "mood_mixer": True
        }
    })

@app.route('/api/gesture/predict', methods=['POST'])
def predict_gesture():
    if not gesture_model or not gesture_scaler:
        return jsonify({"error": "Gesture models not loaded"}), 500
    
    try:
        data = request.get_json()
        image_data = data.get('image')
        if not image_data:
            return jsonify({"error": "No image data provided"}), 400
        
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return jsonify({"error": f"Invalid image data: {str(e)}"}), 400
        
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        rgb_image = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2RGB)
        
        # Debug: Log image dimensions
        print(f"🔍 Image dimensions: {rgb_image.shape}")
        
        results = hands.process(rgb_image)
        
        # Debug: Log hand detection results
        if results.multi_hand_landmarks:
            print(f"✅ Hand detected! Number of hands: {len(results.multi_hand_landmarks)}")
            hand_landmarks = results.multi_hand_landmarks[0]
            print(f"📏 Hand landmarks: {len(hand_landmarks.landmark)} points")
            
            # Debug: Log first few landmark positions
            for i, landmark in enumerate(hand_landmarks.landmark[:5]):
                print(f"   Landmark {i}: x={landmark.x:.3f}, y={landmark.y:.3f}, z={landmark.z:.3f}")
        else:
            print("❌ No hand detected in image")
            return jsonify({"gesture": "none", "confidence": 0.0, "message": "No hand detected"})
        
        hand_landmarks = results.multi_hand_landmarks[0]
        
        # Use your exact feature extraction method
        def to_feature_vec(hand_landmarks):
            base_x = hand_landmarks.landmark[0].x
            base_y = hand_landmarks.landmark[0].y
            vec = []
            for lm in hand_landmarks.landmark:
                vec.append(lm.x - base_x)
                vec.append(lm.y - base_y)
            return np.array(vec, dtype=np.float32).reshape(1, -1)  # (1,42)
        
        features = to_feature_vec(hand_landmarks)
        
        # Debug: Log feature extraction
        print(f"🔢 Features extracted: {features.shape}")
        print(f"   First 5 features: {features[0][:5]}")
        print(f"   Last 5 features: {features[0][-5:]}")
        
        features_scaled = gesture_scaler.transform(features)
        
        # Debug: Log scaling results
        print(f"⚖️ Features scaled: {features_scaled.shape}")
        print(f"   First 5 scaled: {features_scaled[0][:5]}")
        
        if hasattr(gesture_model, 'predict_proba'):
            probabilities = gesture_model.predict_proba(features_scaled)[0]
            predicted_class = gesture_model.classes_[np.argmax(probabilities)]
            confidence = float(np.max(probabilities))
            
            # Debug: Log all class probabilities
            print(f"🎯 Model prediction results:")
            print(f"   Predicted class: {predicted_class}")
            print(f"   Confidence: {confidence:.3f}")
            print(f"   All probabilities:")
            for i, (cls, prob) in enumerate(zip(gesture_model.classes_, probabilities)):
                print(f"     {cls}: {prob:.3f}")
        else:
            predicted_class = gesture_model.predict(features_scaled)[0]
            confidence = 1.0
        
        threshold = getattr(Config, 'GESTURE_CONFIDENCE_THRESHOLD', 0.3)
        
        # Debug: Log threshold comparison
        print(f"🎚️ Confidence threshold: {threshold}")
        print(f"   Confidence {confidence:.3f} {'>=' if confidence >= threshold else '<'} threshold {threshold}")
        
        if confidence < threshold:
            predicted_class = "none"
            confidence = 0.0
            print(f"   ⚠️ Below threshold, setting to 'none'")
        else:
            print(f"   ✅ Above threshold, keeping prediction: {predicted_class}")
        
        return jsonify({
            "gesture": predicted_class,
            "confidence": confidence,
            "probabilities": probabilities.tolist() if hasattr(gesture_model, 'predict_proba') else None,
            "threshold": threshold
        })
        
    except Exception as e:
        print(f"❌ Gesture prediction error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ===== NEW ARTIST MIX ENDPOINTS =====

@app.route('/api/artist-mix/search', methods=['POST'])
def search_artist_mix():
    """
    Search for artist songs in a specific genre and play on Spotify
    
    Request Body:
    {
        "artist": "Artist Name",
        "genre": "Genre Name",
        "limit": 20
    }
    """
    try:
        data = request.json
        artist_name = data.get('artist', '').strip()
        genre = data.get('genre', '').strip()
        limit = data.get('limit', 20)
        
        if not artist_name:
            return jsonify({
                'ok': False,
                'error': 'Artist name is required'
            }), 400
        
        print(f"Searching for artist: {artist_name}, genre: {genre or 'all'}")
        
        # Get Spotify client
        sp = get_spotify_client()
        
        # Check if Spotify is active
        devices = sp.devices()
        if not devices.get('devices'):
            return jsonify({
                'ok': False,
                'error': 'No active Spotify device found. Please open Spotify and start playing something.'
            }), 400
        
        # Search for the artist
        artist_results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
        
        if not artist_results['artists']['items']:
            return jsonify({
                'ok': False,
                'error': f'Artist "{artist_name}" not found'
            }), 404
        
        artist = artist_results['artists']['items'][0]
        artist_id = artist['id']
        artist_full_name = artist['name']
        
        print(f"Found artist: {artist_full_name} (ID: {artist_id})")
        
        # Build search query
        if genre:
            # Search with both artist and genre
            search_query = f'artist:{artist_name} genre:{genre}'
        else:
            # Search just by artist
            search_query = f'artist:{artist_name}'
        
        print(f"Search query: {search_query}")
        
        # Search for tracks
        track_results = sp.search(q=search_query, type='track', limit=limit)
        tracks = track_results['tracks']['items']
        
        if not tracks:
            # Fallback: Get artist's top tracks
            print("No tracks found with genre, falling back to top tracks")
            tracks = sp.artist_top_tracks(artist_id)['tracks'][:limit]
        
        if not tracks:
            return jsonify({
                'ok': False,
                'error': f'No tracks found for {artist_full_name}' + (f' in {genre} genre' if genre else '')
            }), 404
        
        print(f"Found {len(tracks)} tracks")
        
        # Extract track URIs
        track_uris = [track['uri'] for track in tracks]
        
        # Get active device
        active_device = None
        for device in devices['devices']:
            if device['is_active']:
                active_device = device['id']
                break
        
        if not active_device and devices['devices']:
            active_device = devices['devices'][0]['id']
        
        print(f"Using device: {active_device}")
        
        # Start playing the first track
        sp.start_playback(device_id=active_device, uris=[track_uris[0]])
        print(f"Started playing: {tracks[0]['name']}")
        
        # Add remaining tracks to queue
        for uri in track_uris[1:]:
            sp.add_to_queue(uri, device_id=active_device)
        
        print(f"Added {len(track_uris) - 1} tracks to queue")
        
        # Prepare track info for response
        track_info = []
        for track in tracks:
            track_info.append({
                'name': track['name'],
                'artist': ', '.join([a['name'] for a in track['artists']]),
                'album': track['album']['name'],
                'uri': track['uri'],
                'duration_ms': track['duration_ms'],
                'image': track['album']['images'][0]['url'] if track['album']['images'] else None
            })
        
        return jsonify({
            'ok': True,
            'message': f'Playing {len(tracks)} tracks by {artist_full_name}' + (f' in {genre} genre' if genre else ''),
            'artist': artist_full_name,
            'genre': genre,
            'tracks_count': len(tracks),
            'tracks': track_info,
            'now_playing': track_info[0] if track_info else None
        })
        
    except Exception as e:
        print(f"❌ Artist mix search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'ok': False,
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/artist-mix/search-artists', methods=['GET'])
def search_artists():
    """
    Search for artists by name (for autocomplete/suggestions)
    
    Query Parameters:
    - q: Search query
    - limit: Number of results (default 10)
    """
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({
                'ok': False,
                'error': 'Search query is required'
            }), 400
        
        sp = get_spotify_client()
        
        # Search for artists
        results = sp.search(q=f'artist:{query}', type='artist', limit=limit)
        
        artists = []
        for artist in results['artists']['items']:
            artists.append({
                'id': artist['id'],
                'name': artist['name'],
                'genres': artist['genres'],
                'popularity': artist['popularity'],
                'image': artist['images'][0]['url'] if artist['images'] else None,
                'followers': artist['followers']['total']
            })
        
        return jsonify({
            'ok': True,
            'artists': artists,
            'count': len(artists)
        })
    
    except Exception as e:
        print(f"❌ Artist search error: {e}")
        return jsonify({
            'ok': False,
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/api/artist-mix/genres', methods=['GET'])
def get_genres():
    """Get available genres from Spotify"""
    try:
        sp = get_spotify_client()
        
        # Get available genre seeds
        genres = sp.recommendation_genre_seeds()
        
        return jsonify({
            'ok': True,
            'genres': sorted(genres['genres']),
            'count': len(genres['genres'])
        })
    
    except Exception as e:
        print(f"❌ Genre fetch error: {e}")
        # Return fallback genres if Spotify API fails
        fallback_genres = [
            'pop', 'rock', 'hip-hop', 'electronic', 'jazz', 'classical', 
            'country', 'r&b', 'reggae', 'blues', 'folk', 'indie', 
            'alternative', 'metal', 'punk', 'funk', 'soul', 'gospel',
            'latin', 'world', 'ambient', 'dance', 'house', 'techno',
            'trance', 'dubstep', 'trap', 'lo-fi', 'chill', 'acoustic'
        ]
        
        return jsonify({
            'ok': True,
            'genres': sorted(fallback_genres),
            'count': len(fallback_genres),
            'fallback': True,
            'message': 'Using fallback genres due to Spotify API error'
        })

@app.route('/api/artist-mix/play-multiple', methods=['POST'])
def play_multiple_artists():
    """
    Play tracks from multiple artists
    
    Request Body:
    {
        "artists": ["Artist 1", "Artist 2", "Artist 3"],
        "genre": "Genre Name",  # optional
        "tracks_per_artist": 5,  # optional, default 5
        "shuffle": true  # optional, default true
    }
    """
    try:
        data = request.json
        artists = data.get('artists', [])
        genre = data.get('genre', '').strip()
        tracks_per_artist = data.get('tracks_per_artist', 5)
        shuffle = data.get('shuffle', True)
        
        if not artists:
            return jsonify({
                'ok': False,
                'error': 'Artists list is required'
            }), 400
        
        print(f"Playing multiple artists: {artists}, genre: {genre or 'all'}")
        
        # Get Spotify client
        sp = get_spotify_client()
        
        # Check if Spotify is active
        devices = sp.devices()
        if not devices.get('devices'):
            return jsonify({
                'ok': False,
                'error': 'No active Spotify device found. Please open Spotify and start playing something.'
            }), 400
        
        all_tracks = []
        artist_info = {}
        
        # Process each artist
        for artist_name in artists:
            print(f"Processing artist: {artist_name}")
            
            # Search for the artist
            artist_results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
            
            if not artist_results['artists']['items']:
                print(f"Artist '{artist_name}' not found, skipping")
                continue
            
            artist = artist_results['artists']['items'][0]
            artist_id = artist['id']
            artist_full_name = artist['name']
            
            # Build search query
            if genre:
                search_query = f'artist:{artist_name} genre:{genre}'
            else:
                search_query = f'artist:{artist_name}'
            
            # Search for tracks
            track_results = sp.search(q=search_query, type='track', limit=tracks_per_artist)
            tracks = track_results['tracks']['items']
            
            if not tracks:
                # Fallback: Get artist's top tracks
                print(f"No tracks found with genre for {artist_full_name}, using top tracks")
                tracks = sp.artist_top_tracks(artist_id)['tracks'][:tracks_per_artist]
            
            if tracks:
                # Add artist info to tracks
                for track in tracks:
                    track['artist_name'] = artist_full_name
                    track['artist_id'] = artist_id
                
                all_tracks.extend(tracks)
                artist_info[artist_full_name] = {
                    'id': artist_id,
                    'tracks_found': len(tracks)
                }
                print(f"Found {len(tracks)} tracks for {artist_full_name}")
            else:
                print(f"No tracks found for {artist_full_name}")
        
        if not all_tracks:
            return jsonify({
                'ok': False,
                'error': 'No tracks found for any of the specified artists'
            }), 404
        
        # Shuffle tracks if requested
        if shuffle:
            import random
            random.shuffle(all_tracks)
            print("Shuffled tracks")
        
        # Extract track URIs
        track_uris = [track['uri'] for track in all_tracks]
        
        # Get active device
        active_device = None
        for device in devices['devices']:
            if device['is_active']:
                active_device = device['id']
                break
        
        if not active_device and devices['devices']:
            active_device = devices['devices'][0]['id']
        
        print(f"Using device: {active_device}")
        
        # Start playing the first track
        sp.start_playback(device_id=active_device, uris=[track_uris[0]])
        print(f"Started playing: {all_tracks[0]['name']} by {all_tracks[0]['artist_name']}")
        
        # Add remaining tracks to queue
        for uri in track_uris[1:]:
            sp.add_to_queue(uri, device_id=active_device)
        
        print(f"Added {len(track_uris) - 1} tracks to queue")
        
        # Prepare response
        track_info = []
        for track in all_tracks:
            track_info.append({
                'name': track['name'],
                'artist': track['artist_name'],
                'duration_ms': track['duration_ms'],
                'image': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'uri': track['uri']
            })
        
        return jsonify({
            'ok': True,
            'message': f'Playing {len(track_uris)} tracks from {len(artist_info)} artists',
            'artists': list(artist_info.keys()),
            'artist_info': artist_info,
            'tracks': track_info,
            'tracks_count': len(track_uris),
            'genre': genre,
            'shuffled': shuffle
        })
        
    except Exception as e:
        print(f"Error in play_multiple_artists: {e}")
        traceback.print_exc()
        return jsonify({
            'ok': False,
            'error': f'Server error: {str(e)}'
        }), 500

# ===== ARTGIG INTEGRATION ENDPOINTS =====

@app.route('/api/artgig/start', methods=['POST'])
def start_artgig_session():
    """
    Start an artgig DJ session with tag-based music discovery
    
    Request Body:
    {
        "mode": "artist" | "random",
        "tag_profile": "1" | "2" | "3" | "4",  # Tag profile selection
        "artists": ["Artist 1", "Artist 2"],  # Required for artist mode
        "initial_batch": 50,  # optional
        "topup_batch": 20,    # optional
        "changes_per_topup": 10  # optional
    }
    """
    if not spotify_client:
        return jsonify({"error": "Artgig functionality not available"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        mode = data.get('mode', 'random')
        tag_profile = data.get('tag_profile', '1')
        artists = data.get('artists', [])
        
        # Validate inputs
        if mode not in ['random', 'artist']:
            return jsonify({"error": "Invalid mode. Must be 'random' or 'artist'"}), 400
            
        if tag_profile not in TAG_PROFILES:
            return jsonify({"error": f"Invalid tag profile. Must be one of: {list(TAG_PROFILES.keys())}"}), 400
            
        if mode == 'artist' and not artists:
            return jsonify({"error": "Artists list required for artist mode"}), 400
        
        # Get tags from profile
        tags = TAG_PROFILES[tag_profile]
        
        print(f"Starting artgig session: mode={mode}, tag_profile={tag_profile}, artists={artists}")
        print(f"Using tags: {tags}")
        
        # Get Spotify client
        sp = spotify_client()
        
        # Ensure active device
        device_id = ensure_active_device(sp)
        if not device_id:
            return jsonify({
                'ok': False,
                'error': 'No active Spotify device found. Please open Spotify and start playing something.'
            }), 400
        
        # Start the pump loop in a separate thread
        import threading
        import time
        
        def run_pump_loop():
            try:
                pump_loop(sp, device_id, mode, artists, tags)
            except Exception as e:
                print(f"Pump loop error: {e}")
        
        # Start the pump loop thread
        pump_thread = threading.Thread(target=run_pump_loop, daemon=True)
        pump_thread.start()
        
        return jsonify({
            'ok': True,
            'message': f'Started artgig session with {mode} mode and tag profile {tag_profile}',
            'mode': mode,
            'tag_profile': tag_profile,
            'tags': tags,
            'artists': artists if mode == 'artist' else [],
            'device_id': device_id
        })
        
    except Exception as e:
        print(f"Artgig session error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/artgig/tag-profiles', methods=['GET'])
def get_tag_profiles():
    """Get available tag profiles for artgig"""
    try:
        if not TAG_PROFILES:
            return jsonify({"error": "Tag profiles not available"}), 500
            
        # Format profiles for frontend
        profiles = {}
        for key, tags in TAG_PROFILES.items():
            profiles[key] = {
                'tags': tags,
                'name': {
                    '1': 'Remix / Edits',
                    '2': 'Mashup',
                    '3': 'Lofi',
                    '4': 'Slowed + Reverb'
                }.get(key, f'Profile {key}')
            }
        
        return jsonify({
            'ok': True,
            'profiles': profiles
        })
        
    except Exception as e:
        print(f"Tag profiles error: {e}")
        return jsonify({"error": str(e)}), 500

# ===== END ARTGIG INTEGRATION ENDPOINTS =====

# ===== FINA RECOM INTEGRATION ENDPOINTS =====

@app.route('/api/fina-recom/status', methods=['GET'])
def fina_recom_status():
    """Check if Fina Recom system is available and user profile exists"""
    try:
        import os
        import json
        
        # Check if metadata.json exists
        metadata_path = os.path.join(os.path.dirname(__file__), '..', 'fina recom', 'metadata.json')
        profile_exists = os.path.exists(metadata_path)
        
        status = {
            "available": True,
            "profile_exists": profile_exists,
            "metadata_path": metadata_path
        }
        
        if profile_exists:
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    status["profile_info"] = {
                        "user_name": profile.get("user", {}).get("name", "Unknown"),
                        "top_artists_count": len(profile.get("top_artists", {}).get("long_term", [])),
                        "top_tracks_count": len(profile.get("top_tracks", {}).get("long_term", [])),
                        "genres_count": len(profile.get("top_genres_all_time", [])),
                        "playlists_summary": bool(profile.get("playlists_summary", {}).get("top_artists"))
                    }
            except Exception as e:
                status["profile_error"] = str(e)
        
        return jsonify({
            "ok": True,
            "status": status
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"Failed to check Fina Recom status: {str(e)}"
        }), 500

@app.route('/api/fina-recom/generate-profile', methods=['POST'])
def fina_recom_generate_profile():
    """Generate user profile using combocode.py"""
    try:
        import subprocess
        import os
        import json
        
        # Path to combocode.py
        combocode_path = os.path.join(os.path.dirname(__file__), '..', 'fina recom', 'combocode.py')
        
        if not os.path.exists(combocode_path):
            return jsonify({
                "ok": False,
                "error": "Fina Recom system not found"
            }), 404
        
        # Run combocode.py
        result = subprocess.run(
            [sys.executable, combocode_path],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(combocode_path)
        )
        
        if result.returncode != 0:
            return jsonify({
                "ok": False,
                "error": f"Profile generation failed: {result.stderr}",
                "stdout": result.stdout
            }), 500
        
        # Check if metadata.json was created
        metadata_path = os.path.join(os.path.dirname(combocode_path), 'metadata.json')
        if not os.path.exists(metadata_path):
            return jsonify({
                "ok": False,
                "error": "Profile generation completed but metadata.json not found"
            }), 500
        
        # Load and return profile summary
        with open(metadata_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        return jsonify({
            "ok": True,
            "message": "Profile generated successfully",
            "profile_summary": {
                "user_name": profile.get("user", {}).get("name", "Unknown"),
                "top_artists_count": len(profile.get("top_artists", {}).get("long_term", [])),
                "top_tracks_count": len(profile.get("top_tracks", {}).get("long_term", [])),
                "genres_count": len(profile.get("top_genres_all_time", [])),
                "playlists_summary": bool(profile.get("playlists_summary", {}).get("top_artists"))
            }
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"Failed to generate profile: {str(e)}"
        }), 500

@app.route('/api/fina-recom/start-recommendations', methods=['POST'])
def fina_recom_start_recommendations():
    """Start Fina Recom recommendation system"""
    try:
        import subprocess
        import os
        import threading
        import time
        
        data = request.get_json() or {}
        mode = data.get('mode', 'balanced')
        
        # Validate mode
        valid_modes = ['comfort', 'balanced', 'explorer']
        if mode not in valid_modes:
            return jsonify({
                "ok": False,
                "error": f"Invalid mode. Must be one of: {valid_modes}"
            }), 400
        
        # Path to newmodel.py
        newmodel_path = os.path.join(os.path.dirname(__file__), '..', 'fina recom', 'newmodel.py')
        
        if not os.path.exists(newmodel_path):
            return jsonify({
                "ok": False,
                "error": "Fina Recom system not found"
            }), 404
        
        # Check if metadata.json exists
        metadata_path = os.path.join(os.path.dirname(newmodel_path), 'metadata.json')
        if not os.path.exists(metadata_path):
            return jsonify({
                "ok": False,
                "error": "User profile not found. Please generate profile first."
            }), 400
        
        # Start the recommendation system in a separate thread
        def run_recommendations():
            try:
                # Create a subprocess with the mode as input
                process = subprocess.Popen(
                    [sys.executable, newmodel_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.path.dirname(newmodel_path)
                )
                
                # Send the mode selection
                mode_input = "1" if mode == "comfort" else "2" if mode == "balanced" else "3"
                stdout, stderr = process.communicate(input=mode_input)
                
                if process.returncode != 0:
                    print(f"Fina Recom error: {stderr}")
                else:
                    print(f"Fina Recom completed: {stdout}")
                    
            except Exception as e:
                print(f"Fina Recom thread error: {e}")
        
        # Start the thread
        thread = threading.Thread(target=run_recommendations, daemon=True)
        thread.start()
        
        return jsonify({
            "ok": True,
            "message": f"Fina Recom started in {mode} mode",
            "mode": mode,
            "status": "running"
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"Failed to start recommendations: {str(e)}"
        }), 500

@app.route('/api/fina-recom/profile', methods=['GET'])
def fina_recom_get_profile():
    """Get user profile data"""
    try:
        import os
        import json
        
        metadata_path = os.path.join(os.path.dirname(__file__), '..', 'fina recom', 'metadata.json')
        
        if not os.path.exists(metadata_path):
            return jsonify({
                "ok": False,
                "error": "Profile not found. Please generate profile first."
            }), 404
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        # Return a cleaned version of the profile (remove sensitive data)
        cleaned_profile = {
            "user": profile.get("user", {}),
            "top_artists": profile.get("top_artists", {}),
            "top_tracks": profile.get("top_tracks", {}),
            "top_albums": profile.get("top_albums", []),
            "top_genres_all_time": profile.get("top_genres_all_time", []),
            "playlists_summary": profile.get("playlists_summary", {}),
            "eras": profile.get("eras", {})
        }
        
        return jsonify({
            "ok": True,
            "profile": cleaned_profile
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"Failed to load profile: {str(e)}"
        }), 500

# ===== END FINA RECOM INTEGRATION ENDPOINTS =====

# ===== MOOD MIXER INTEGRATION ENDPOINTS =====

@app.route('/api/mood-mixer/start', methods=['POST'])
def start_mood_mixer():
    """
    Start the Spotify Mood Mixer with custom mood weights and language selection
    
    Request Body:
    {
        "language": "hi" | "en" | "mix",
        "mood_weights": {
            "happy": 20,
            "sad_breakup": 10,
            "motivational": 15,
            "chill_lofi": 15,
            "hiphop": 10,
            "rap": 10,
            "old_classic": 10,
            "romantic": 5,
            "party": 5
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        language = data.get('language', 'mix')
        mood_weights = data.get('mood_weights', {})
        
        # Validate language
        if language not in ['hi', 'en', 'mix']:
            return jsonify({"error": "Invalid language. Must be 'hi', 'en', or 'mix'"}), 400
        
        # Validate mood weights
        valid_moods = ['happy', 'sad_breakup', 'motivational', 'chill_lofi', 'hiphop', 'rap', 'old_classic', 'romantic', 'party']
        total_weight = 0
        
        for mood in valid_moods:
            weight = mood_weights.get(mood, 0)
            if weight < 0 or weight > 100 or weight % 5 != 0:
                return jsonify({"error": f"Invalid weight for {mood}. Must be 0-100, multiple of 5"}), 400
            total_weight += weight
        
        if total_weight != 100:
            return jsonify({"error": f"Total weight must equal 100, got {total_weight}"}), 400
        
        # Get Spotify client
        sp = get_spotify_client()
        
        # Check if Spotify is active
        devices = sp.devices()
        if not devices.get('devices'):
            return jsonify({
                'ok': False,
                'error': 'No active Spotify device found. Please open Spotify and start playing something.'
            }), 400
        
        # Get active device
        active_device = None
        for device in devices['devices']:
            if device['is_active']:
                active_device = device['id']
                break
        
        if not active_device and devices['devices']:
            active_device = devices['devices'][0]['id']
        
        # Start the mood mixer in a separate thread
        import threading
        import time
        
        def run_mood_mixer():
            try:
                # Import the mood mixer functions
                import sys
                import os
                
                # Add the Models directory to Python path to find mood_mixer.py
                models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Models')
                if models_dir not in sys.path:
                    sys.path.insert(0, models_dir)
                
                print(f"🔍 Looking for mood_mixer.py in: {models_dir}")
                print(f"🔍 Current working directory: {os.getcwd()}")
                print(f"🔍 Python path includes: {sys.path[:3]}...")
                
                # Check if mood_mixer.py exists
                mood_mixer_path = os.path.join(models_dir, 'mood_mixer.py')
                if os.path.exists(mood_mixer_path):
                    print(f"✅ Found mood_mixer.py at: {mood_mixer_path}")
                else:
                    print(f"❌ mood_mixer.py not found at: {mood_mixer_path}")
                    raise FileNotFoundError(f"mood_mixer.py not found at {mood_mixer_path}")
                
                # Import the mood mixer functions from mood_mixer.py
                from mood_mixer import (
                    build_batch, start_with_seed_then_queue, monitor_and_topup,
                    SEED_START, INITIAL_BATCH, TOP_UP_EVERY, TOP_UP_BATCH
                )
                print("✅ Successfully imported mood_mixer.py functions")
                
                # Build initial batch
                seen_uris = set()
                seed = build_batch(sp, language, mood_weights, SEED_START, seen_uris, first_page_only=True)
                for tr in seed: 
                    seen_uris.add(tr["uri"])
                
                # Build the remainder of the initial batch
                remaining_needed = max(0, INITIAL_BATCH - len(seed))
                rest = []
                if remaining_needed > 0:
                    rest = build_batch(sp, language, mood_weights, remaining_needed, seen_uris, first_page_only=False)
                    for tr in rest: 
                        seen_uris.add(tr["uri"])
                
                print(f"Starting mood mixer with {len(seed)} seed tracks, then queuing {len(rest)} more")
                start_with_seed_then_queue(sp, active_device, seed, rest)
                
                # Monitor and top-up
                monitor_and_topup(sp, active_device, language, mood_weights, seen_uris, next_topup_after=TOP_UP_EVERY)
                
            except Exception as e:
                print(f"Mood mixer error: {e}")
                import traceback
                traceback.print_exc()
        
        # Start the mood mixer thread
        mixer_thread = threading.Thread(target=run_mood_mixer, daemon=True)
        mixer_thread.start()
        
        return jsonify({
            'ok': True,
            'message': f'Started mood mixer with {language} language',
            'language': language,
            'mood_weights': mood_weights,
            'device_id': active_device
        })
        
    except Exception as e:
        print(f"Mood mixer error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/mood-mixer/moods', methods=['GET'])
def get_mood_categories():
    """Get available mood categories and their display names"""
    try:
        moods = [
            {"key": "happy", "name": "Happy ☀", "description": "Upbeat, cheerful music"},
            {"key": "sad_breakup", "name": "Sad / Breakup 💔", "description": "Emotional, melancholic tracks"},
            {"key": "motivational", "name": "Motivational ⚡", "description": "Energetic, inspiring music"},
            {"key": "chill_lofi", "name": "Chill / Lo-Fi 🌿", "description": "Relaxed, ambient tracks"},
            {"key": "hiphop", "name": "Hip Hop 🎧", "description": "Hip hop genre"},
            {"key": "rap", "name": "Rap 🔥", "description": "Rap music"},
            {"key": "old_classic", "name": "Old / Classic 📼", "description": "Vintage and classic songs"},
            {"key": "romantic", "name": "Romantic ❤", "description": "Love songs and romantic tracks"},
            {"key": "party", "name": "Party / Dance 🎉", "description": "High-energy party music"}
        ]
        
        return jsonify({
            'ok': True,
            'moods': moods,
            'total_moods': len(moods)
        })
        
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': f'Failed to get mood categories: {str(e)}'
        }), 500

@app.route('/api/mood-mixer/languages', methods=['GET'])
def get_language_options():
    """Get available language options"""
    try:
        languages = [
            {"key": "hi", "name": "Hindi 🇮🇳", "description": "Hindi music only"},
            {"key": "en", "name": "English 🇬🇧", "description": "English music only"},
            {"key": "mix", "name": "Mixed 🌍", "description": "Both Hindi and English music"}
        ]
        
        return jsonify({
            'ok': True,
            'languages': languages
        })
        
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': f'Failed to get language options: {str(e)}'
        }), 500

# ===== END MOOD MIXER INTEGRATION ENDPOINTS =====

# ===== END ARTIST MIX ENDPOINTS =====

@app.route('/api/spotify/dj/start', methods=['POST'])
def start_dj_session():
    """Start a DJ session with the specified parameters"""
    if not dj_run_once:
        return jsonify({"error": "DJ functionality not available"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        mode = data.get('mode', 'random')
        genre = data.get('genre', 'Remix')
        artists = data.get('artists', [])
        batch_size = data.get('batch_size', getattr(Config, 'DJ_DEFAULT_BATCH_SIZE', 150))
        strict_primary = data.get('strict_primary', getattr(Config, 'DJ_STRICT_PRIMARY', True))
        
        # Validate inputs
        if mode not in ['random', 'artist']:
            return jsonify({"error": "Invalid mode. Must be 'random' or 'artist'"}), 400
            
        if genre not in ['Remix', 'LOFI', 'Mashup']:
            return jsonify({"error": "Invalid genre. Must be 'Remix', 'LOFI', or 'Mashup'"}), 400
            
        if mode == 'artist' and not artists:
            return jsonify({"error": "Artists list required for artist mode"}), 400
        
        # Call the DJ function
        result = dj_run_once(
            mode=mode,
            genre=genre,
            artists=artists,
            batch_size=batch_size,
            strict_primary=strict_primary
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"DJ session error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": str(datetime.datetime.now()),
        "gesture_models": gesture_model is not None,
        "dj_module": dj_run_once is not None,
        "artist_mix": True,
        "config": {
            "gesture_confidence_threshold": getattr(Config, 'GESTURE_CONFIDENCE_THRESHOLD', 0.8),
            "dj_batch_size": getattr(Config, 'DJ_DEFAULT_BATCH_SIZE', 150)
        }
    })

@app.route('/api/gesture/classes')
def get_gesture_classes():
    """Get available gesture classes"""
    if not gesture_model:
        return jsonify({"error": "Gesture model not loaded"}), 500
    
    classes = gesture_model.classes_.tolist() if hasattr(gesture_model, 'classes_') else []
    return jsonify({
        "classes": classes,
        "total_classes": len(classes),
        "confidence_threshold": getattr(Config, 'GESTURE_CONFIDENCE_THRESHOLD', 0.8)
    })

@app.route('/api/config')
def get_config():
    """Get current configuration (non-sensitive)"""
    return jsonify({
        "gesture_recognition": {
            "confidence_threshold": getattr(Config, 'GESTURE_CONFIDENCE_THRESHOLD', 0.8),
            "stable_frames": getattr(Config, 'GESTURE_STABLE_FRAMES', 5),
            "action_cooldown": getattr(Config, 'GESTURE_ACTION_COOLDOWN', 1.0)
        },
        "dj": {
            "default_batch_size": getattr(Config, 'DJ_DEFAULT_BATCH_SIZE', 150),
            "strict_primary": getattr(Config, 'DJ_STRICT_PRIMARY', True)
        },
        "server": {
            "host": getattr(Config, 'HOST', '0.0.0.0'),
            "port": getattr(Config, 'PORT', 5000),
            "debug": getattr(Config, 'DEBUG', True)
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ===== Spotify OAuth (server-managed) =====

@app.get('/api/spotify/status')
def spotify_status():
    try:
        oauth = _spotify_oauth()
        token_info = oauth.get_cached_token()
        is_authed = bool(token_info)
        status = {"authenticated": is_authed}
        if is_authed:
            sp = spotipy.Spotify(auth=token_info['access_token'])
            try:
                me = sp.current_user()
                status["user"] = {"id": me.get('id'), "name": me.get('display_name') or me.get('id')}
                devices = sp.devices().get('devices', [])
                status["devices"] = [{"id": d.get('id'), "name": d.get('name'), "is_active": d.get('is_active')} for d in devices]
            except Exception:
                pass
        return jsonify(status)
    except Exception as e:
        return jsonify({"authenticated": False, "error": str(e)}), 500

@app.get('/api/spotify/login')
def spotify_login():
    try:
        oauth = _spotify_oauth()
        auth_url = oauth.get_authorize_url()
        return jsonify({"auth_url": auth_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get('/callback')
def spotify_callback():
    try:
        oauth = _spotify_oauth()
        if not oauth:
            return jsonify({"error": "Spotify OAuth not configured"}), 500
            
        code = request.args.get('code')
        state = request.args.get('state')
        if not code:
            return jsonify({"error": "Missing authorization code"}), 400
            
        token_info = oauth.get_access_token(code)
        # Persisted via cache_path; redirect back to frontend with success
        frontend_url = getattr(Config, 'SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:5500/frontend/profile.html')
        return redirect(f"{frontend_url}?auth=success&expires_in={token_info.get('expires_in', 0)}")
    except Exception as e:
        print(f"Spotify callback error: {e}")
        frontend_url = getattr(Config, 'SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:5500/frontend/profile.html')
        return redirect(f"{frontend_url}?auth=error&message={str(e)}")

@app.post('/api/spotify/play')
def spotify_play_specific():
    """Play a specific track given a Spotify URI or search query."""
    try:
        data = request.get_json(force=True)
        uri = (data or {}).get('uri')
        query = (data or {}).get('query')
        oauth = _spotify_oauth()
        token = oauth.get_cached_token()
        if not token:
            return jsonify({"ok": False, "error": "Not authenticated"}), 401
        sp = spotipy.Spotify(auth=token['access_token'])

        # resolve device
        devices = sp.devices().get('devices', [])
        if not devices:
            return jsonify({"ok": False, "error": "No active Spotify device"}), 400
        device_id = None
        for d in devices:
            if d.get('is_active'):
                device_id = d.get('id'); break
        if not device_id:
            device_id = devices[0].get('id')
            try:
                sp.transfer_playback(device_id=device_id, force_play=True)
            except Exception:
                pass

        target_uri = uri
        if not target_uri and query:
            res = sp.search(q=query, type='track', limit=1)
            items = ((res or {}).get('tracks') or {}).get('items') or []
            if not items:
                return jsonify({"ok": False, "error": "Track not found"}), 404
            target_uri = items[0].get('uri')

        if not target_uri:
            return jsonify({"ok": False, "error": "Provide 'uri' or 'query'"}), 400

        sp.start_playback(device_id=device_id, uris=[target_uri])
        return jsonify({"ok": True, "played": target_uri})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post('/api/spotify/control')
def spotify_control():
    """Generic control endpoint for playback actions from gestures/UI.
    Body: { "action": "play|pause|next|previous|volume|seek", "delta": 10| -10 | 30000 }
    """
    try:
        data = request.get_json(force=True) or {}
        action = (data.get('action') or '').lower()
        delta = int(data.get('delta') or 0)

        oauth = _spotify_oauth()
        token = oauth.get_cached_token()
        if not token:
            return jsonify({"ok": False, "error": "Not authenticated"}), 401
        sp = spotipy.Spotify(auth=token['access_token'])

        devices = sp.devices().get('devices', [])
        if not devices:
            return jsonify({"ok": False, "error": "No active Spotify device"}), 400
        device = next((d for d in devices if d.get('is_active')), devices[0])
        device_id = device.get('id')

        if action == 'play':
            sp.start_playback(device_id=device_id)
        elif action == 'pause':
            sp.pause_playback(device_id=device_id)
        elif action == 'next':
            sp.next_track(device_id=device_id)
        elif action == 'previous':
            sp.previous_track(device_id=device_id)
        elif action == 'volume':
            cur_v = device.get('volume_percent', 50)
            new_v = max(0, min(100, cur_v + (delta if delta else 0)))
            sp.volume(new_v, device_id=device_id)
        elif action == 'seek':
            pb = sp.current_playback()
            if not pb or not pb.get('item'):
                return jsonify({"ok": False, "error": "No current playback"}), 400
            pos = pb.get('progress_ms', 0)
            dur = pb['item'].get('duration_ms', 0)
            new_pos = min(max(0, pos + (delta if delta else 0)), max(0, dur - 1000))
            sp.seek_track(new_pos, device_id=device_id)
        elif action == 'like':
            # Like/save current track
            pb = sp.current_playback()
            if not pb or not pb.get('item'):
                return jsonify({"ok": False, "error": "No current playback"}), 400
            track_id = pb['item'].get('id')
            if track_id:
                sp.current_user_saved_tracks_add([track_id])
            else:
                return jsonify({"ok": False, "error": "No track ID"}), 400
        else:
            return jsonify({"ok": False, "error": "Unknown action"}), 400

        return jsonify({"ok": True, "action": action})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get('/api/spotify/current')
def spotify_current():
    """Get currently playing track information with metadata and progress"""
    try:
        oauth = _spotify_oauth()
        token = oauth.get_cached_token()
        if not token:
            return jsonify({"ok": False, "error": "Not authenticated"}), 401
        
        sp = spotipy.Spotify(auth=token['access_token'])
        playback = sp.current_playback()
        
        if not playback:
            return jsonify({"ok": True, "playing": False, "message": "No active playback"})
        
        track = playback.get('item', {})
        if not track:
            return jsonify({"ok": True, "playing": False, "message": "No track information"})
        
        # Extract track information
        track_info = {
            "id": track.get('id'),
            "name": track.get('name'),
            "artists": [artist.get('name') for artist in track.get('artists', [])],
            "album": track.get('album', {}).get('name'),
            "duration_ms": track.get('duration_ms'),
            "external_urls": track.get('external_urls', {}),
            "preview_url": track.get('preview_url')
        }
        
        # Extract album art
        images = track.get('album', {}).get('images', [])
        if images:
            track_info['album_art'] = images[0].get('url')  # Get largest image
        
        # Extract playback state
        playback_info = {
            "is_playing": playback.get('is_playing', False),
            "progress_ms": playback.get('progress_ms', 0),
            "volume_percent": playback.get('device', {}).get('volume_percent', 0),
            "shuffle_state": playback.get('shuffle_state', False),
            "repeat_state": playback.get('repeat_state', 'off'),
            "device": {
                "id": playback.get('device', {}).get('id'),
                "name": playback.get('device', {}).get('name'),
                "type": playback.get('device', {}).get('type'),
                "is_active": playback.get('device', {}).get('is_active', False)
            }
        }
        
        return jsonify({
            "ok": True,
            "playing": True,
            "track": track_info,
            "playback": playback_info
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get('/api/spotify/devices')
def spotify_devices():
    """Get available Spotify devices"""
    try:
        oauth = _spotify_oauth()
        token = oauth.get_cached_token()
        if not token:
            return jsonify({"ok": False, "error": "Not authenticated"}), 401
        
        sp = spotipy.Spotify(auth=token['access_token'])
        devices = sp.devices().get('devices', [])
        
        return jsonify({
            "ok": True,
            "devices": devices
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post('/api/spotify/transfer')
def spotify_transfer():
    """Transfer playback to a specific device"""
    try:
        data = request.get_json(force=True) or {}
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({"ok": False, "error": "Device ID required"}), 400
        
        oauth = _spotify_oauth()
        token = oauth.get_cached_token()
        if not token:
            return jsonify({"ok": False, "error": "Not authenticated"}), 401
        
        sp = spotipy.Spotify(auth=token['access_token'])
        sp.transfer_playback(device_id=device_id, force_play=True)
        
        return jsonify({"ok": True, "device_id": device_id})
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Print startup information
    print("🎵 Smart Music Backend Starting...")
    print(f"📍 Server will run on {getattr(Config, 'HOST', '0.0.0.0')}:{getattr(Config, 'PORT', 5000)}")
    print(f"🔧 Gesture models: {'✅ Loaded' if gesture_model else '❌ Not loaded'}")
    print(f"🎧 DJ functionality: {'✅ Available' if dj_run_once else '❌ Not available'}")
    print(f"🎤 Artist Mix: ✅ Available")
    print(f"🎵 Mood Mixer: ✅ Available")
    print("-" * 50)
    
    app.run(
        debug=getattr(Config, 'DEBUG', True),
        host=getattr(Config, 'HOST', '0.0.0.0'),
        port=getattr(Config, 'PORT', 3000)
    )