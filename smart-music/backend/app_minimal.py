from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json

# Add the gesture models path
sys.path.append('../Gesture final')

# Import your existing modules
try:
    from Models.Models.artists_gig_backfriend import run_once as dj_run_once
    print("✅ DJ module imported successfully")
except ImportError as e:
    print(f"Warning: DJ module not available: {e}")
    dj_run_once = None

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:5000'])

# Try to load gesture models (optional)
gesture_model = None
gesture_scaler = None

try:
    import joblib
    MODEL_PATH = "../Gesture final/gesture_model.pkl"
    SCALER_PATH = "../Gesture final/scaler.pkl"
    
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        gesture_model = joblib.load(MODEL_PATH)
        gesture_scaler = joblib.load(SCALER_PATH)
        print("✅ Gesture models loaded successfully")
    else:
        print("⚠️  Gesture model files not found - gesture recognition disabled")
except ImportError:
    print("⚠️  joblib not available - gesture recognition disabled")
except Exception as e:
    print(f"⚠️  Error loading gesture models: {e}")

# Try to initialize MediaPipe (optional)
hands = None
try:
    import mediapipe as mp
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )
    print("✅ MediaPipe Hands initialized")
except ImportError:
    print("⚠️  MediaPipe not available - gesture recognition disabled")
except Exception as e:
    print(f"⚠️  Error initializing MediaPipe: {e}")

@app.route('/')
def index():
    return jsonify({
        "message": "Smart Music Backend API (Minimal)", 
        "status": "running",
        "version": "1.0.0",
        "features": {
            "gesture_recognition": gesture_model is not None and hands is not None,
            "dj_control": dj_run_once is not None,
            "spotify_integration": True
        }
    })

@app.route('/api/gesture/predict', methods=['POST'])
def predict_gesture():
    """Predict gesture from image data"""
    if not gesture_model or not gesture_scaler or not hands:
        return jsonify({
            "error": "Gesture recognition not available",
            "gesture": "none",
            "confidence": 0.0,
            "message": "Gesture recognition requires ML dependencies"
        }), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({"error": "No image data provided"}), 400
        
        # For now, return a mock response since we don't have full ML setup
        return jsonify({
            "gesture": "none",
            "confidence": 0.0,
            "message": "Gesture recognition in minimal mode - install full dependencies for full functionality"
        })
        
    except Exception as e:
        print(f"Gesture prediction error: {e}")
        return jsonify({"error": str(e)}), 500

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
        batch_size = data.get('batch_size', 150)
        strict_primary = data.get('strict_primary', True)
        
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
    import datetime
    return jsonify({
        "status": "healthy",
        "timestamp": str(datetime.datetime.now()),
        "gesture_models": gesture_model is not None,
        "mediapipe_hands": hands is not None,
        "dj_module": dj_run_once is not None,
        "mode": "minimal"
    })

@app.route('/api/gesture/classes')
def get_gesture_classes():
    """Get available gesture classes"""
    if not gesture_model:
        return jsonify({
            "error": "Gesture model not loaded",
            "classes": [],
            "total_classes": 0,
            "message": "Install full dependencies for gesture recognition"
        }), 503
    
    classes = gesture_model.classes_.tolist() if hasattr(gesture_model, 'classes_') else []
    return jsonify({
        "classes": classes,
        "total_classes": len(classes),
        "confidence_threshold": 0.8
    })

@app.route('/api/config')
def get_config():
    """Get current configuration (non-sensitive)"""
    return jsonify({
        "gesture_recognition": {
            "available": gesture_model is not None and hands is not None,
            "confidence_threshold": 0.8,
            "stable_frames": 5,
            "action_cooldown": 1.0
        },
        "dj": {
            "available": dj_run_once is not None,
            "default_batch_size": 150,
            "strict_primary": True
        },
        "server": {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": True,
            "mode": "minimal"
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    import datetime
    
    # Print startup information
    print("🎵 Smart Music Backend Starting (Minimal Mode)...")
    print("📍 Server will run on 0.0.0.0:5000")
    print(f"🔧 Gesture models: {'✅ Loaded' if gesture_model else '❌ Not loaded'}")
    print(f"🤖 MediaPipe Hands: {'✅ Available' if hands else '❌ Not available'}")
    print(f"🎧 DJ functionality: {'✅ Available' if dj_run_once else '❌ Not available'}")
    print("💡 This is minimal mode - some features may be limited")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
