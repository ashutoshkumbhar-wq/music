import os
from dotenv import load_dotenv

# Load environment variables from backend/.env explicitly (robust on Windows)
_DOTENV_PATH = os.path.join(os.path.dirname(__file__), '.env')
# Force override so .env values win over empty or stale system env vars
load_dotenv(_DOTENV_PATH, override=True)

class Config:
    """Configuration class for the Smart Music Backend"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Spotify API credentials
    # Workaround for UTF-8 BOM on first line of .env on Windows
    _cid = os.environ.get('SPOTIPY_CLIENT_ID')
    if not _cid:
        _cid_bom = os.environ.get('\ufeffSPOTIPY_CLIENT_ID')
        if _cid_bom:
            os.environ['SPOTIPY_CLIENT_ID'] = _cid_bom
            _cid = _cid_bom
    SPOTIPY_CLIENT_ID = _cid
    SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
    SPOTIPY_REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:5500/frontend/profile.html')
    
    # Gesture recognition settings
    GESTURE_CONFIDENCE_THRESHOLD = float(os.environ.get('GESTURE_CONFIDENCE_THRESHOLD', 0.3))  # Lowered from 0.8 to 0.3
    GESTURE_STABLE_FRAMES = int(os.environ.get('GESTURE_STABLE_FRAMES', '5'))
    GESTURE_ACTION_COOLDOWN = float(os.environ.get('GESTURE_ACTION_COOLDOWN', '1.0'))
    
    # DJ settings
    DJ_DEFAULT_BATCH_SIZE = int(os.environ.get('DJ_DEFAULT_BATCH_SIZE', '150'))
    DJ_STRICT_PRIMARY = os.environ.get('DJ_STRICT_PRIMARY', '1') == '1'
    
    # Model paths
    GESTURE_MODEL_PATH = os.environ.get('GESTURE_MODEL_PATH', '../Gesture final/gesture_model.pkl')
    GESTURE_SCALER_PATH = os.environ.get('GESTURE_SCALER_PATH', '../Gesture final/scaler.pkl')
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000,http://localhost:5500,http://127.0.0.1:5500,null').split(',')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.SPOTIPY_CLIENT_ID:
            errors.append("SPOTIPY_CLIENT_ID is required")
        
        if not cls.SPOTIPY_CLIENT_SECRET:
            errors.append("SPOTIPY_CLIENT_SECRET is required")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print current configuration (without sensitive data)"""
        print("🔧 Smart Music Backend Configuration:")
        print(f"   Host: {cls.HOST}")
        print(f"   Port: {cls.PORT}")
        print(f"   Debug: {cls.DEBUG}")
        print(f"   Spotify Client ID: {'Set' if cls.SPOTIPY_CLIENT_ID else 'Not Set'}")
        print(f"   Spotify Client Secret: {'Set' if cls.SPOTIPY_CLIENT_SECRET else 'Not Set'}")
        print(f"   Gesture Confidence Threshold: {cls.GESTURE_CONFIDENCE_THRESHOLD}")
        print(f"   DJ Default Batch Size: {cls.DJ_DEFAULT_BATCH_SIZE}")
        print(f"   CORS Origins: {cls.CORS_ORIGINS}")

# Create a .env template if it doesn't exist
def create_env_template():
    """Create a .env template file"""
    env_template = """# Smart Music Backend Environment Variables
# Copy this file to .env and fill in your values

# Flask Settings
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True
HOST=0.0.0.0
PORT=5000

# Spotify API Credentials
SPOTIPY_CLIENT_ID=your_spotify_client_id_here
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIPY_REDIRECT_URI=http://localhost:5000/callback

# Gesture Recognition Settings
GESTURE_CONFIDENCE_THRESHOLD=0.8
GESTURE_STABLE_FRAMES=5
GESTURE_ACTION_COOLDOWN=1.0

# DJ Settings
DJ_DEFAULT_BATCH_SIZE=150
DJ_STRICT_PRIMARY=1

# Model Paths (relative to backend directory)
GESTURE_MODEL_PATH=../Gesture final/gesture_model.pkl
GESTURE_SCALER_PATH=../Gesture final/scaler.pkl

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000
"""
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write(env_template)
        print(f"📝 Created .env template at {env_path}")
        print("   Please edit this file with your actual values")

if __name__ == "__main__":
    create_env_template()
    Config.print_config()
    
    errors = Config.validate()
    if errors:
        print("\n❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("\n✅ Configuration is valid")
