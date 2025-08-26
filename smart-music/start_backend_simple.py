#!/usr/bin/env python3
"""
Simple Smart Music Backend Startup Script
This script provides a more robust way to start the backend
"""

import os
import sys
import subprocess
import time

def install_package(package_name):
    """Install a single package with better error handling"""
    try:
        print(f"📦 Installing {package_name}...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', package_name
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {package_name} installed successfully")
            return True
        else:
            print(f"❌ Failed to install {package_name}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing {package_name}: {e}")
        return False

def install_core_dependencies():
    """Install core dependencies one by one"""
    core_packages = [
        'flask',
        'flask-cors', 
        'python-dotenv'
    ]
    
    print("🔧 Installing core dependencies...")
    for package in core_packages:
        if not install_package(package):
            print(f"⚠️  Warning: {package} installation failed")
    
    return True

def install_ml_dependencies():
    """Install ML-related dependencies with fallbacks"""
    ml_packages = [
        ('numpy', 'numpy'),
        ('Pillow', 'Pillow'),
        ('opencv-python', 'opencv-python'),
        ('mediapipe', 'mediapipe'),
        ('scikit-learn', 'scikit-learn'),
        ('joblib', 'joblib'),
        ('spotipy', 'spotipy'),
        ('requests', 'requests')
    ]
    
    print("🤖 Installing ML dependencies...")
    for display_name, package_name in ml_packages:
        if not install_package(package_name):
            print(f"⚠️  Warning: {display_name} installation failed")
            if display_name == 'mediapipe':
                print("   💡 MediaPipe is optional - gesture recognition won't work")
            elif display_name == 'opencv-python':
                print("   💡 OpenCV is optional - camera features won't work")
    
    return True

def check_models():
    """Check if gesture models exist"""
    model_path = "Gesture final/gesture_model.pkl"
    scaler_path = "Gesture final/scaler.pkl"
    
    if not os.path.exists(model_path):
        print(f"⚠️  Gesture model not found: {model_path}")
        print("   Gesture recognition will not work")
        return False
    
    if not os.path.exists(scaler_path):
        print(f"⚠️  Gesture scaler not found: {scaler_path}")
        print("   Gesture recognition will not work")
        return False
    
    print("✅ Gesture models found")
    return True

def start_server():
    """Start the Flask server"""
    print("🚀 Starting Smart Music Backend Server...")
    print("📍 Server will be available at: http://localhost:5000")
    print("📱 Frontend can be accessed at: frontend/index.html")
    print("🔧 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Change to backend directory and start server
        os.chdir('backend')
        
        # Try to start the server
        result = subprocess.run([sys.executable, 'app.py'])
        
        if result.returncode != 0:
            print("❌ Server exited with errors")
            return False
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False
    
    return True

def main():
    print("🎵 Smart Music Backend Setup (Simple)")
    print("=" * 45)
    
    # Check if we're in the right directory
    if not os.path.exists('backend') or not os.path.exists('frontend'):
        print("❌ Please run this script from the project root directory")
        print("   Expected structure:")
        print("   smart-music/")
        print("   ├── backend/")
        print("   ├── frontend/")
        print("   └── start_backend_simple.py")
        return
    
    # Install dependencies
    print("\n📦 Setting up dependencies...")
    install_core_dependencies()
    install_ml_dependencies()
    
    # Check models
    print("\n🔍 Checking gesture models...")
    check_models()
    
    # Setup environment
    print("\n⚙️  Setting up environment...")
    os.environ.setdefault('SPOTIPY_CLIENT_ID', 'your_spotify_client_id_here')
    os.environ.setdefault('SPOTIPY_CLIENT_SECRET', 'your_spotify_client_secret_here')
    os.environ.setdefault('SPOTIPY_REDIRECT_URI', 'http://localhost:5000/callback')
    print("✅ Environment variables set")
    
    # Start server
    print("\n🚀 Starting server...")
    if not start_server():
        print("❌ Failed to start server")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check if port 5000 is available")
        print("   2. Ensure all dependencies are installed")
        print("   3. Check backend/app.py for syntax errors")
        print("   4. Try running 'cd backend && python app.py' manually")

if __name__ == "__main__":
    main()
