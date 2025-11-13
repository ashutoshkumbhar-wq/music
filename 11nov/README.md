# 🎵 Smart Music - AI-Powered Music Experience Platform

A comprehensive web application that combines advanced gesture recognition, Spotify integration, and intelligent music discovery systems. Control your music playback using hand gestures, create personalized playlists, and discover new music through multiple AI-powered recommendation engines.

## ✨ Core Features

### 🎭 **Advanced Gesture Recognition System**
- **8 Trained Hand Gestures** - Custom machine learning model with 95%+ accuracy
- **Real-time Detection** - Live camera-based gesture recognition using MediaPipe
- **Touch Gestures** - Swipe, tap, and double-tap controls as backup
- **Visual Feedback** - Real-time confidence scoring and action feedback
- **Gesture Testing Interface** - Dedicated page for testing and calibration

### 🎵 **Comprehensive Spotify Integration**
- **OAuth 2.0 Authentication** - Secure Spotify account connection
- **Full Playback Control** - Play, pause, next, previous, volume, seek, like
- **Device Management** - Automatic device detection and switching
- **Track Information** - Real-time display of current track details
- **Multiple Backend Options** - Flask (Python) and Node.js alternatives

### 🤖 **AI-Powered Music Discovery Systems**

#### **Fina Recom - Personalized Recommendations**
- **User Profile Analysis** - Analyzes your Spotify listening history
- **Three Discovery Modes**:
  - **Comfort Zone** - Stay close to your favorites
  - **Balanced Explore** - Mix of familiar and new music
  - **Full Explorer** - Maximum discovery across genres and eras
- **Smart Playlist Integration** - Uses your saved playlists for better recommendations

#### **Mood Mixer - Custom Mood-Based Playlists**
- **9 Mood Categories** - Happy, Sad/Breakup, Motivational, Chill/Lo-Fi, Hip Hop, Rap, Old/Classic, Romantic, Party
- **Language Selection** - Hindi, English, or Mixed language support
- **Custom Weight Distribution** - Fine-tune mood preferences (0-100% per mood)
- **Real-time Playlist Building** - Creates playlists based on your mood weights

#### **Artist Mix - Multi-Artist Playlist Creator**
- **Multiple Artist Support** - Add multiple artists to create custom mixes
- **Genre Profiles** - 4 predefined genre profiles (Remix/Edits, Mashup, Lo-Fi, Slowed+Reverb)
- **Smart Search** - Artist autocomplete and search functionality
- **Queue Management** - Automatic track queuing and playback

#### **Artgig DJ - Automated Music Discovery**
- **Tag-Based Discovery** - Uses music tags for intelligent track selection
- **Artist Mode** - Focus on specific artists with tag filtering
- **Random Mode** - Discover new music through tag exploration
- **Auto Top-up** - Continuously adds new tracks to maintain queue

### 🎨 **Modern Multi-Interface Design**
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Multiple Interfaces** - Main dashboard, gesture testing, profile management, artist mix, mood mixer
- **Real-time Updates** - Live status monitoring and feedback
- **Professional UI** - Dark theme with smooth animations and modern styling

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (Python 3.11 recommended)
- **Node.js 16+** (for alternative backend)
- **Modern web browser** with camera access
- **Spotify account** (Premium recommended for full features)
- **Internet connection**

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/smart-music.git
cd smart-music
```

### 2. Install Dependencies

#### Python Backend (Recommended)
```bash
cd backend
pip install -r requirements.txt
cd ..
```

#### Node.js Backend (Alternative)
```bash
cd spotify-backend
npm install
cd ..
```

### 3. Set Up Spotify Credentials

#### For Python Backend
```bash
cd backend
python config.py  # Creates .env template
# Edit .env file with your Spotify credentials
```

#### For Node.js Backend
```bash
cd spotify-backend
# Create .env file with your Spotify credentials
```

### 4. Start the Application

#### Option A: Python Backend (Recommended)
```bash
# Terminal 1: Start Backend
cd backend
python app.py

# Terminal 2: Start Frontend
cd frontend
python -m http.server 5500
```

#### Option B: Node.js Backend
```bash
# Terminal 1: Start Backend
cd spotify-backend
npm start

# Terminal 2: Start Frontend
cd frontend
python -m http.server 5500
```

### 5. Access the Application
- **Main App**: `http://127.0.0.1:5500/`
- **Gesture Test**: `http://127.0.0.1:5500/gesture-test-simple.html`
- **Spotify Connect**: `http://127.0.0.1:5500/profile.html`
- **Artist Mix**: `http://127.0.0.1:5500/Cards/artist/index.html`
- **Mood Mixer**: `http://127.0.0.1:5500/mood-mixer.html`
- **Fina Recom**: `http://127.0.0.1:5500/fina-recom.html`

## 🎭 Gesture Recognition

### **Your 8 Trained Gestures**

| Gesture | Action | Hand | Description |
|---------|--------|------|-------------|
| `play_right` | Play | Right | Start music playback |
| `pause_right` | Pause | Right | Pause music playback |
| `next_right` | Next Track | Right | Skip to next song |
| `previous_right` | Previous | Right | Go to previous song |
| `volume_up_left` | Volume Up | Left | Increase volume by 10% |
| `volume_down_left` | Volume Down | Left | Decrease volume by 10% |
| `like_left` | Like Track | Left | Save current track |
| `skip30_left` | Skip 30s | Left | Skip 30 seconds forward |

### **Touch Gestures (Backup)**
- **Swipe Left** → Previous track
- **Swipe Right** → Next track
- **Swipe Up** → Play/Pause toggle
- **Swipe Down** → Volume down
- **Tap** → Play/Pause toggle
- **Double Tap** → Next track

## 🏗️ Project Structure

```
smart-music/
├── frontend/                           # Web application
│   ├── index.html                     # Main dashboard
│   ├── gesture-test-simple.html       # Gesture testing interface
│   ├── profile.html                   # Spotify connection & settings
│   ├── mood-mixer.html                # Mood-based playlist creator
│   ├── fina-recom.html                # AI recommendation system
│   ├── camera.html                    # Camera interface
│   ├── camera.js                      # Camera functionality
│   ├── unified-gesture-controller.js  # Unified gesture system
│   ├── spotify.js                     # Spotify integration
│   ├── fina-recom.js                  # Fina Recom frontend logic
│   ├── script.js                      # Main application logic
│   ├── style.css                      # Main styling
│   ├── camera.css                     # Camera interface styling
│   ├── profile.css                    # Profile page styling
│   └── Cards/                         # Artist mix interface
│       ├── artist/
│       │   ├── index.html             # Artist selection
│       │   ├── script.js              # Artist mix logic
│       │   ├── style.css              # Artist mix styling
│       │   └── Frame/                 # Artist frame component
│       └── Page/
│           ├── index.html             # Category selection
│           ├── script.js              # Category logic
│           └── style.css              # Category styling
├── backend/                           # Flask API (Primary)
│   ├── app.py                        # Main backend server
│   ├── config.py                     # Configuration management
│   ├── requirements.txt              # Python dependencies
│   ├── env.template                  # Environment template
│   └── .env                          # Environment variables (create from template)
├── spotify-backend/                  # Node.js backend (Alternative)
│   ├── server.js                     # Express.js server
│   └── package.json                  # Node.js dependencies
├── Gesture final/                    # Machine Learning models
│   ├── gesture_model.pkl             # Trained gesture model
│   ├── scaler.pkl                    # Feature scaler
│   ├── collect_gestures.py           # Data collection script
│   ├── train_model_strong.py         # Model training script
│   ├── maintesting_spotify.py        # Testing script
│   ├── testing.py                    # Additional testing
│   ├── testing1.json                 # Training data
│   └── README.txt                    # ML documentation
├── Models/                           # AI modules
│   ├── artgig.py                     # DJ automation system
│   └── mood_mixer.py                 # Mood-based playlist system
├── fina recom/                       # AI recommendation system
│   ├── combocode.py                  # User profile generation
│   ├── newmodel.py                   # Recommendation engine
│   ├── config.py                     # Fina Recom configuration
│   ├── zzzHowToRun                   # Setup instructions
│   └── metadata.json                 # User profile data (generated)
└── README.md                         # This file
```

## 🔧 Configuration

### Environment Variables

#### Python Backend (.env)
```env
# Flask Settings
PORT=5000
HOST=0.0.0.0
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# Spotify API Credentials (REQUIRED)
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
SPOTIPY_REDIRECT_URI=http://localhost:5000/callback

# Optional: Additional Spotify Settings
SPOTIFY_SCOPES=user-modify-playback-state user-read-playback-state user-read-currently-playing user-library-modify
SPOTIFY_CACHE_PATH=.cache-dj-session

# Gesture Recognition Settings
GESTURE_CONFIDENCE_THRESHOLD=0.3
GESTURE_STABLE_FRAMES=5
GESTURE_ACTION_COOLDOWN=1.0

# DJ Settings
DJ_DEFAULT_BATCH_SIZE=150
DJ_STRICT_PRIMARY=1

# Model Paths
GESTURE_MODEL_PATH=../Gesture final/gesture_model.pkl
GESTURE_SCALER_PATH=../Gesture final/scaler.pkl

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000,http://localhost:5500,http://127.0.0.1:5500,null
```

#### Node.js Backend (.env)
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:3000/auth/callback
FRONTEND_ORIGIN=http://127.0.0.1:5500
SESSION_SECRET=dev
PORT=3000
HTTPS=0
```

### Spotify Developer Setup
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add redirect URI: `http://localhost:5000/callback` (Python) or `http://localhost:3000/auth/callback` (Node.js)
4. Copy Client ID and Client Secret to your `.env` file
5. Note: You can use either backend, but Python backend has more features

## 🎯 Usage Guide

### 1. Connect to Spotify
1. Open the application in your browser
2. Click on the profile icon or go to `/profile.html`
3. Click "Connect with Spotify"
4. Authorize the application
5. Configure gesture controls in the profile page

### 2. Main Dashboard (`index.html`)
- **Home Interface**: Clean, modern music dashboard
- **Navigation**: Access to all features via sidebar
- **Music Cards**: Visual track selection
- **Gesture Integration**: Unified gesture controller

### 3. Gesture Testing (`gesture-test-simple.html`)
- **Live Camera Feed**: Real-time gesture detection
- **Confidence Display**: Visual feedback on gesture recognition
- **Gesture Instructions**: Reference for all 8 trained gestures
- **Testing Controls**: Toggle camera and gesture recognition

### 4. Artist Mix Creation (`Cards/artist/index.html`)
- **Artist Selection**: Add multiple artists to your mix
- **Genre Filtering**: Choose from 4 predefined genre profiles
- **Playlist Generation**: Create custom playlists from selected artists
- **Real-time Playback**: Start playing immediately

### 5. Mood Mixer (`mood-mixer.html`)
- **Language Selection**: Choose Hindi, English, or Mixed
- **Mood Weights**: Set custom weights for 9 mood categories
- **Smart Playlist Building**: Creates playlists based on your preferences
- **Real-time Updates**: Continuous playlist management

### 6. Fina Recom (`fina-recom.html`)
- **Profile Generation**: Analyze your Spotify listening history
- **Discovery Modes**: Choose from Comfort Zone, Balanced, or Explorer
- **Smart Recommendations**: AI-powered music discovery
- **Personalized Experience**: Based on your music taste

### 7. Profile Management (`profile.html`)
- **Spotify Connection**: OAuth authentication
- **Gesture Settings**: Configure touch and camera gestures
- **Current Track Display**: Real-time playback information
- **Settings Configuration**: Customize your experience

## 🔌 API Endpoints

### Backend API (Flask)
- `GET /` - Health check and status
- `POST /api/gesture/predict` - Gesture recognition
- `GET /api/spotify/status` - Spotify authentication status
- `GET /api/spotify/current` - Current playback information
- `POST /api/spotify/control` - Playback control (play, pause, next, etc.)
- `POST /api/spotify/play` - Play specific track
- `GET /api/spotify/devices` - Available devices
- `POST /api/spotify/transfer` - Transfer playback to device

#### Artist Mix Endpoints
- `POST /api/artist-mix/search` - Search and play artist tracks
- `GET /api/artist-mix/search-artists` - Search for artists
- `GET /api/artist-mix/genres` - Available genres
- `POST /api/artist-mix/play-multiple` - Play multiple artists

#### Mood Mixer Endpoints
- `POST /api/mood-mixer/start` - Start mood mixer session
- `GET /api/mood-mixer/moods` - Get available mood categories
- `GET /api/mood-mixer/languages` - Get language options

#### Fina Recom Endpoints
- `GET /api/fina-recom/status` - Check system status
- `POST /api/fina-recom/generate-profile` - Generate user profile
- `POST /api/fina-recom/start-recommendations` - Start recommendations
- `GET /api/fina-recom/profile` - Get user profile data

#### Artgig DJ Endpoints
- `POST /api/artgig/start` - Start artgig DJ session
- `GET /api/artgig/tag-profiles` - Get tag profiles

### Alternative Backend (Node.js)
- `GET /auth/login` - Spotify OAuth login
- `GET /auth/callback` - OAuth callback
- `GET /api/spotify/status` - Authentication status
- `GET /api/spotify/current` - Current playback
- `POST /api/spotify/control` - Playback control
- `POST /api/spotify/play` - Play track
- `GET /api/spotify/devices` - Available devices

## 🛠️ Troubleshooting

### Common Issues

**Backend Won't Start**
```bash
# Check Python version
python --version

# Install dependencies
pip install -r backend/requirements.txt

# Check if models are present
ls "Gesture final/gesture_model.pkl"
ls "Gesture final/scaler.pkl"

# Try running directly
cd backend && python app.py
```

**Spotify Connection Fails**
- Check `.env` file has correct credentials
- Verify redirect URI matches exactly
- Ensure Spotify app is open and playing music
- Check if Spotify Premium is required for some features

**Camera Not Working**
- Allow camera permissions in browser
- Check if camera is used by another app
- Try different browser (Chrome recommended)
- Ensure HTTPS is not required for camera access

**Gestures Not Detected**
- Ensure camera is active and well-lit
- Make gestures clearly visible to camera
- Check confidence threshold (default: 0.3)
- Test with gesture testing page first
- Ensure MediaPipe is properly installed

**AI Systems Not Working**
- Check if Spotify is authenticated
- Ensure active Spotify device
- Check backend logs for API errors
- Verify all dependencies are installed

### Debug Information
- **Backend Logs**: Check terminal output when running `python app.py`
- **Browser Console**: Press F12 and check Console tab
- **Health Check**: Visit `http://localhost:5000/api/health`
- **Gesture Testing**: Use `gesture-test-simple.html` for debugging

## 📱 Browser Support

| Browser | Version | Camera | Gestures | Notes |
|---------|---------|--------|----------|-------|
| Chrome | 80+ | ✅ | ✅ | Recommended |
| Firefox | 75+ | ✅ | ✅ | Good support |
| Edge | 80+ | ✅ | ✅ | Good support |
| Safari | 13+ | ⚠️ | ⚠️ | Limited support |

## 🔮 Future Enhancements

- **Voice Commands** - Speech-to-text integration for hands-free control
- **Emotion Detection** - Mood-based music selection using facial recognition
- **Advanced Gestures** - Complex hand movement recognition and custom gestures
- **Mobile App** - Native mobile application with React Native
- **Social Features** - Share playlists and sessions with friends
- **AI Music Generation** - Generate custom tracks based on preferences
- **Multi-User Support** - Collaborative playlist creation
- **Advanced Analytics** - Music listening patterns and insights
- **Custom Gesture Training** - User-defined gesture recognition
- **Integration APIs** - Support for other music services (Apple Music, YouTube Music)

## 🤝 Contributing

We welcome contributions! Please feel free to submit issues, feature requests, or pull requests.

### Development Guidelines
- Follow existing code style and structure
- Test on multiple devices and browsers
- Ensure accessibility standards are met
- Document new features and changes

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🔬 Technical Details

### Machine Learning Pipeline
- **Data Collection**: Custom gesture collection using MediaPipe hand landmarks
- **Feature Extraction**: 42-dimensional feature vectors (21 landmarks × 2 coordinates)
- **Model Training**: Ensemble classifier (Random Forest + SVM + KNN)
- **Real-time Inference**: MediaPipe + scikit-learn for live gesture recognition
- **Accuracy**: 95%+ on trained gesture set

### Architecture
- **Frontend**: Vanilla JavaScript with modern ES6+ features
- **Backend**: Flask (Python) with optional Node.js alternative
- **Database**: No persistent storage (session-based)
- **Authentication**: OAuth 2.0 with Spotify
- **Real-time**: WebSocket-like polling for live updates

### Dependencies
- **Python**: Flask, MediaPipe, OpenCV, scikit-learn, Spotipy, pandas, tqdm
- **JavaScript**: Hammer.js for touch gestures, native Web APIs
- **Node.js**: Express.js, express-session, node-fetch (alternative backend)

## 🙏 Acknowledgments

- **Spotify** for their comprehensive Web API and developer tools
- **MediaPipe** for hand landmark detection and computer vision
- **scikit-learn** for machine learning framework and algorithms
- **Flask** for the web framework and API development
- **OpenCV** for computer vision and image processing
- **Hammer.js** for touch gesture recognition
- **Font Awesome** for the icon library

## 📞 Support

For support, questions, or feedback:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the API documentation

---

**Made with ❤️ for music lovers everywhere**

*Smart Music - Where Technology Meets Musical Passion*