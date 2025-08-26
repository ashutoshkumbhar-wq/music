# 🎵 Smart Music Backend

This is the Flask backend server that powers the Smart Music application, providing gesture recognition, DJ control, and Spotify integration.

## 🚀 Features

- **Gesture Recognition API**: Real-time hand gesture detection using ML models
- **DJ Control System**: Automated music queue management with Spotify
- **Spotify Integration**: Full Spotify API integration for music control
- **RESTful API**: Clean, documented endpoints for frontend integration
- **Configuration Management**: Environment-based configuration system

## 📋 Prerequisites

- Python 3.8+
- Spotify Developer Account
- Webcam (for gesture recognition)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd smart-music
```

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file in the backend directory:

```bash
# Copy the template
cp config.py .env

# Edit with your values
nano .env
```

Required environment variables:
```env
# Spotify API Credentials
SPOTIPY_CLIENT_ID=your_spotify_client_id_here
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIPY_REDIRECT_URI=http://localhost:5000/callback

# Optional: Customize settings
GESTURE_CONFIDENCE_THRESHOLD=0.8
DJ_DEFAULT_BATCH_SIZE=150
```

### 4. Get Spotify Credentials
1. Go to [Spotify Developer Console](https://developer.spotify.com/console/)
2. Create a new app
3. Copy Client ID and Client Secret
4. Add `http://localhost:5000/callback` to Redirect URIs

## 🚀 Running the Server

### Option 1: Use the Startup Script (Recommended)
```bash
# From project root
python start_backend.py
```

### Option 2: Direct Flask Run
```bash
cd backend
python app.py
```

### Option 3: Flask Development Server
```bash
cd backend
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run --host=0.0.0.0 --port=5000
```

## 📡 API Endpoints

### Base URL
```
http://localhost:5000
```

### Endpoints

#### Health Check
```
GET /api/health
```
Returns server health status and loaded modules.

#### Gesture Recognition
```
POST /api/gesture/predict
```
Predicts gesture from base64-encoded image data.

**Request Body:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
}
```

**Response:**
```json
{
  "gesture": "play_right",
  "confidence": 0.95,
  "probabilities": [0.01, 0.95, 0.04],
  "threshold": 0.8
}
```

#### DJ Session Control
```
POST /api/spotify/dj/start
```
Starts a DJ session with specified parameters.

**Request Body:**
```json
{
  "mode": "random",
  "genre": "Remix",
  "artists": [],
  "batch_size": 150,
  "strict_primary": true
}
```

**Response:**
```json
{
  "ok": true,
  "mode": "random",
  "genre": "Remix",
  "batch": 150,
  "hint": "Random · Remix",
  "started": 1,
  "queued": 149
}
```

#### Configuration
```
GET /api/config
```
Returns current configuration settings.

#### Gesture Classes
```
GET /api/gesture/classes
```
Returns available gesture classes and confidence threshold.

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SPOTIPY_CLIENT_ID` | Required | Spotify Client ID |
| `SPOTIPY_CLIENT_SECRET` | Required | Spotify Client Secret |
| `SPOTIPY_REDIRECT_URI` | `http://localhost:5000/callback` | Spotify redirect URI |
| `GESTURE_CONFIDENCE_THRESHOLD` | `0.8` | Minimum confidence for gesture recognition |
| `GESTURE_STABLE_FRAMES` | `5` | Frames required for stable gesture detection |
| `GESTURE_ACTION_COOLDOWN` | `1.0` | Cooldown between gesture actions (seconds) |
| `DJ_DEFAULT_BATCH_SIZE` | `150` | Default number of tracks to queue |
| `DJ_STRICT_PRIMARY` | `1` | Only use primary artist for filtering |
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `5000` | Server port |

### Configuration File
The `config.py` file provides a centralized configuration system. You can modify it to add new settings or override defaults.

## 🎭 Gesture Recognition

### Supported Gestures
The system recognizes 8 main gestures:

**Right Hand (Playback Control):**
- `play_right`: Play music
- `pause_right`: Pause music
- `next_right`: Next track
- `previous_right`: Previous track

**Left Hand (Utility Control):**
- `volume_up_left`: Increase volume
- `volume_down_left`: Decrease volume
- `like_left`: Like current track
- `skip30_left`: Skip 30 seconds forward

### How It Works
1. **Image Capture**: Frontend captures webcam frames
2. **Feature Extraction**: MediaPipe extracts 42 hand landmarks
3. **ML Prediction**: Trained model predicts gesture class
4. **Confidence Filtering**: Only high-confidence gestures are accepted
5. **Action Mapping**: Gestures are mapped to Spotify actions

### Model Files
- `gesture_model.pkl`: Trained machine learning model
- `scaler.pkl`: Feature scaling parameters

## 🎧 DJ System

### Modes
- **Random Mode**: Generates random tracks based on genre tags
- **Artist Mode**: Generates tracks from specific artists

### Genres
- **Remix**: Remixes, bootlegs, VIPs, festival mixes
- **LOFI**: Chill, study, sleep, ambient beats
- **Mashup**: Blends, DJ mixes, party mashups

### Features
- Automatic deduplication
- Genre-based filtering
- Artist validation
- Batch queue management
- Error handling and retries

## 🔍 Troubleshooting

### Common Issues

#### 1. Gesture Models Not Loading
```
❌ Error loading gesture models: [Errno 2] No such file or directory
```
**Solution**: Ensure `gesture_model.pkl` and `scaler.pkl` exist in the `Gesture final/` directory.

#### 2. Spotify Authentication Failed
```
❌ DJ Session failed: No active Spotify device
```
**Solution**: 
- Ensure Spotify is running and playing music
- Check Spotify API credentials
- Verify redirect URI matches exactly

#### 3. Import Errors
```
Warning: DJ module not available
```
**Solution**: Ensure all Python dependencies are installed and the Models directory structure is correct.

#### 4. CORS Issues
```
Access to fetch at 'http://localhost:5000/api/gesture/predict' from origin 'http://localhost:3000' has been blocked
```
**Solution**: Check CORS configuration in `config.py` and ensure frontend origin is included.

### Debug Mode
Enable debug mode for detailed error messages:
```bash
export FLASK_DEBUG=1
```

### Logs
Check console output for detailed error messages and debugging information.

## 🧪 Testing

### Test the API
```bash
# Health check
curl http://localhost:5000/api/health

# Get configuration
curl http://localhost:5000/api/config

# Get gesture classes
curl http://localhost:5000/api/gesture/classes
```

### Test Gesture Recognition
Use the frontend camera interface or send a POST request with a base64 image to `/api/gesture/predict`.

### Test DJ System
Send a POST request to `/api/spotify/dj/start` with valid parameters.

## 📚 Development

### Project Structure
```
backend/
├── app.py              # Main Flask application
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .env               # Environment variables (create this)
```

### Adding New Features
1. Add new routes in `app.py`
2. Update configuration in `config.py` if needed
3. Add new dependencies to `requirements.txt`
4. Update this README

### Code Style
- Follow PEP 8 Python style guidelines
- Add docstrings to all functions
- Use type hints where appropriate
- Handle errors gracefully

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review console logs
3. Verify configuration
4. Create an issue with detailed error information

---

**Happy coding! 🎵✨**
