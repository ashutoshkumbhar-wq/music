#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
import os

print("🔍 Testing Smart Music Backend Imports")
print("=" * 40)

# Test basic packages
print("\n📦 Testing basic packages...")
try:
    import flask
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")

try:
    import flask_cors
    print("✅ Flask-CORS imported successfully")
except ImportError as e:
    print(f"❌ Flask-CORS import failed: {e}")

try:
    import numpy
    print("✅ NumPy imported successfully")
except ImportError as e:
    print(f"❌ NumPy import failed: {e}")

try:
    import cv2
    print("✅ OpenCV imported successfully")
except ImportError as e:
    print(f"❌ OpenCV import failed: {e}")

try:
    import mediapipe as mp
    print("✅ MediaPipe imported successfully")
except ImportError as e:
    print(f"❌ MediaPipe import failed: {e}")

try:
    import joblib
    print("✅ Joblib imported successfully")
except ImportError as e:
    print(f"❌ Joblib import failed: {e}")

try:
    import sklearn
    print(f"✅ Scikit-learn imported successfully (version: {sklearn.__version__})")
except ImportError as e:
    print(f"❌ Scikit-learn import failed: {e}")

try:
    import spotipy
    print("✅ Spotipy imported successfully")
except ImportError as e:
    print(f"❌ Spotipy import failed: {e}")

# Test gesture models
print("\n🤖 Testing gesture models...")
try:
    sys.path.append('Gesture final')
    gesture_model = joblib.load('Gesture final/gesture_model.pkl')
    print("✅ Gesture model loaded successfully")
    print(f"   Model type: {type(gesture_model)}")
    print(f"   Classes: {gesture_model.classes_ if hasattr(gesture_model, 'classes_') else 'N/A'}")
except Exception as e:
    print(f"❌ Gesture model loading failed: {e}")

try:
    gesture_scaler = joblib.load('Gesture final/scaler.pkl')
    print("✅ Gesture scaler loaded successfully")
    print(f"   Scaler type: {type(gesture_scaler)}")
except Exception as e:
    print(f"❌ Gesture scaler loading failed: {e}")

# Test DJ module
print("\n🎧 Testing DJ module...")
try:
    sys.path.append('Models/Models')
    from artists_gig_backfriend import run_once as dj_run_once
    print("✅ DJ module imported successfully")
    print(f"   Function type: {type(dj_run_once)}")
except Exception as e:
    print(f"❌ DJ module import failed: {e}")

# Test MediaPipe Hands
print("\n✋ Testing MediaPipe Hands...")
try:
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )
    print("✅ MediaPipe Hands initialized successfully")
except Exception as e:
    print(f"❌ MediaPipe Hands initialization failed: {e}")

print("\n" + "=" * 40)
print("🎯 Import test completed!")
