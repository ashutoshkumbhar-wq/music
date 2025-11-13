This Folder contains 3 main phases of code:

Dataset Collection

collect_gestures.py
Opens webcam → captures hand landmarks → saves labeled samples into testing1.json.
Used only during training. Backend does not need this.


Model Training

train_model_strong.py
Loads testing1.json → trains ensemble classifier (RF+SVM+KNN) → outputs:
gesture_model.pkl (trained model)
scaler.pkl (feature scaler)
Used only when re-training. Backend does not need this in production.


Runtime / Integration

maintesting1.py (real-time gesture prediction, local only)
maintesting_spotify.py (gesture → Spotify controller)

These scripts:
Load gesture_model.pkl + scaler.pkl
Use MediaPipe Hands to extract 42-dim wrist-relative features
Predict gesture label (e.g., play_right, volume_up_left, none)
Map gestures to Spotify actions


✅ What the Backend Actually Needs
For integration, backend developers only need:

Artifacts:
gesture_model.pkl
scaler.pkl

Preprocessing spec:
Input = 42 floats [x0,y0, x1,y1, ..., x20,y20] (landmarks relative to wrist)
Output = gesture label (string) + probability distribution
Threshold: usually 0.80, reject low-confidence or "none"
Example inference code:
model  = joblib.load("gesture_model.pkl")
scaler = joblib.load("scaler.pkl")


🔑 Summary for Backend
You don’t need dataset collection or training scripts.
You do need the model artifacts (gesture_model.pkl, scaler.pkl) and the preprocessing rule (42 features).
The backend can expose an API /predict that takes features=[42 floats] and returns {label, confidence, probs}.