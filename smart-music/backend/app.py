from flask import Flask, request, jsonify, send_from_directory
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
    print("✅ DJ module imported successfully")
except ImportError as e:
    print(f"Warning: DJ module not available: {e}")
    dj_run_once = None

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:5000', 'null'])

# Load gesture recognition models
MODEL_PATH = getattr(Config, 'GESTURE_MODEL_PATH', "../Gesture final/gesture_model.pkl")
SCALER_PATH = getattr(Config, 'GESTURE_SCALER_PATH', "../Gesture final/scaler.pkl")

try:
    gesture_model = joblib.load(MODEL_PATH)
    gesture_scaler = joblib.load(SCALER_PATH)
    print("✅ Gesture models loaded successfully")
except Exception as e:
    print(f"❌ Error loading gesture models: {e}")
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

@app.route('/')
def index():
    return jsonify({
        "message": "Smart Music Backend API", 
        "status": "running",
        "version": "1.0.0",
        "features": {
            "gesture_recognition": gesture_model is not None,
            "dj_control": dj_run_once is not None,
            "spotify_integration": True
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
        base_x = hand_landmarks.landmark[0].x
        base_y = hand_landmarks.landmark[0].y
        
        # Debug: Log base coordinates
        print(f"📍 Base coordinates: x={base_x:.3f}, y={base_y:.3f}")
        
        features = []
        for landmark in hand_landmarks.landmark:
            features.append(landmark.x - base_x)
            features.append(landmark.y - base_y)
        
        # Debug: Log feature extraction
        print(f"🔢 Features extracted: {len(features)} values")
        print(f"   First 5 features: {features[:5]}")
        print(f"   Last 5 features: {features[-5:]}")
        
        features_scaled = gesture_scaler.transform([features])
        
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

if __name__ == '__main__':
    import datetime
    
    # Print startup information
    print("🎵 Smart Music Backend Starting...")
    print(f"📍 Server will run on {getattr(Config, 'HOST', '0.0.0.0')}:{getattr(Config, 'PORT', 5000)}")
    print(f"🔧 Gesture models: {'✅ Loaded' if gesture_model else '❌ Not loaded'}")
    print(f"🎧 DJ functionality: {'✅ Available' if dj_run_once else '❌ Not available'}")
    print("-" * 50)
    
    app.run(
        debug=getattr(Config, 'DEBUG', True),
        host=getattr(Config, 'HOST', '0.0.0.0'),
        port=getattr(Config, 'PORT', 5000)
    )
