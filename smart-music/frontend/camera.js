const video = document.getElementById('video');
const overlay = document.getElementById('overlay');
const ctx = overlay.getContext('2d');

const toggleCamBtn = document.getElementById('toggleCamBtn');
const cameraToggle = document.getElementById('cameraToggle');
const placeholder = document.getElementById('placeholder');

let stream = null;
let isGestureRecognitionActive = false;
let gestureRecognitionInterval = null;

// Backend API configuration
const BACKEND_URL = 'http://localhost:5000';

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false
    });
    video.srcObject = stream;
    placeholder.style.display = "none";
    toggleCamBtn.classList.add("active");
    toggleCamBtn.classList.remove("off");
    cameraToggle.checked = true;
    resizeCanvas();
    requestAnimationFrame(drawOverlay);
    
    // Start gesture recognition if enabled
    if (isGestureRecognitionActive) {
      startGestureRecognition();
    }
  } catch (err) {
    console.error(err);
    alert("Error accessing camera. Please allow permissions.");
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
  placeholder.style.display = "grid";
  toggleCamBtn.classList.remove("active");
  toggleCamBtn.classList.remove("active");
  toggleCamBtn.classList.add("off");
  cameraToggle.checked = false;
  
  // Stop gesture recognition
  stopGestureRecognition();
}

function resizeCanvas() {
  const rect = video.getBoundingClientRect();
  overlay.width = rect.width * devicePixelRatio;
  overlay.height = rect.height * devicePixelRatio;
  overlay.style.width = rect.width + "px";
  overlay.style.height = rect.height + "px";
  ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
}

window.addEventListener('resize', resizeCanvas);

function drawOverlay() {
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  requestAnimationFrame(drawOverlay);
}

// Gesture recognition functions
async function predictGesture() {
  if (!video.srcObject) return;
  
  try {
    console.log('🔄 Predicting gesture...'); // Debug log
    
    // Capture frame from video
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    // Convert to base64
    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    console.log('📸 Frame captured, size:', imageData.length); // Debug log
    
    // Send to backend
    const response = await fetch(`${BACKEND_URL}/api/gesture/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ image: imageData })
    });
    
    console.log('📡 Backend response status:', response.status); // Debug log
    
    if (response.ok) {
      const result = await response.json();
      console.log('🎯 Gesture prediction result:', result); // Debug log
      updateGestureDisplay(result);
    } else {
      console.error('❌ Backend error:', response.status, response.statusText);
      const errorText = await response.text();
      console.error('Error details:', errorText);
    }
  } catch (error) {
    console.error('❌ Gesture prediction error:', error);
  }
}

function updateGestureDisplay(result) {
  console.log('🔄 Updating gesture display with:', result); // Debug log
  
  // Find all gesture display elements (there are multiple in the HTML)
  const gestureElements = document.querySelectorAll('#currentGesture');
  const confidenceFills = document.querySelectorAll('.confidence-fill');
  
  console.log('🎯 Gesture elements found:', gestureElements.length); // Debug log
  console.log('🎯 Confidence fills found:', confidenceFills.length); // Debug log
  
  // Update all gesture display elements
  gestureElements.forEach(element => {
    if (result.gesture === 'none') {
      element.textContent = 'No gesture detected';
      element.style.color = '#888';
      console.log('📝 Updated gesture display: No gesture detected'); // Debug log
    } else {
      element.textContent = `${result.gesture} (${(result.confidence * 100).toFixed(1)}%)`;
      element.style.color = result.confidence > 0.8 ? '#4CAF50' : '#FF9800';
      console.log('📝 Updated gesture display:', result.gesture, result.confidence); // Debug log
    }
  });
  
  // Update all confidence bars
  confidenceFills.forEach(fill => {
    fill.style.width = `${result.confidence * 100}%`;
    fill.style.backgroundColor = result.confidence > 0.8 ? '#4CAF50' : 
                                result.confidence > 0.6 ? '#FF9800' : '#F44336';
    console.log('📊 Updated confidence bar:', result.confidence); // Debug log
  });
  
  if (gestureElements.length === 0) {
    console.error('❌ No gesture elements found!'); // Debug log
  }
  if (confidenceFills.length === 0) {
    console.error('❌ No confidence fill elements found!'); // Debug log
  }
}

function startGestureRecognition() {
  if (gestureRecognitionInterval) return;
  
  gestureRecognitionInterval = setInterval(predictGesture, 500); // Predict every 500ms
  console.log('Gesture recognition started');
}

function stopGestureRecognition() {
  if (gestureRecognitionInterval) {
    clearInterval(gestureRecognitionInterval);
    gestureRecognitionInterval = null;
    console.log('Gesture recognition stopped');
  }
}

// Toggle gesture recognition
function toggleGestureRecognition() {
  isGestureRecognitionActive = !isGestureRecognitionActive;
  
  if (isGestureRecognitionActive && stream) {
    startGestureRecognition();
  } else {
    stopGestureRecognition();
  }
  
  // Update UI
  const gestureToggle = document.getElementById('gestureToggle');
  if (gestureToggle) {
    gestureToggle.textContent = isGestureRecognitionActive ? 'Stop Gesture Recognition' : 'Start Gesture Recognition';
    gestureToggle.classList.toggle('active', isGestureRecognitionActive);
  }
}

// Icon button click
toggleCamBtn.addEventListener('click', () => {
  stream ? stopCamera() : startCamera();
});

// Toggle switch change
cameraToggle.addEventListener('change', () => {
  cameraToggle.checked ? startCamera() : stopCamera();
});

// Add gesture recognition toggle button
document.addEventListener('DOMContentLoaded', () => {
  const gestureToggle = document.createElement('button');
  gestureToggle.id = 'gestureToggle';
  gestureToggle.textContent = 'Start Gesture Recognition';
  gestureToggle.style.cssText = `
    position: absolute;
    top: 20px;
    left: 20px;
    padding: 10px 20px;
    background: #4CAF50;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 14px;
    z-index: 1000;
  `;
  gestureToggle.addEventListener('click', toggleGestureRecognition);
  document.body.appendChild(gestureToggle);
});

// Health check on load
async function checkBackendHealth() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/health`);
    if (response.ok) {
      const health = await response.json();
      console.log('Backend health:', health);
      
      if (!health.gesture_models) {
        console.warn('Gesture models not loaded on backend');
      }
    }
  } catch (error) {
    console.error('Backend health check failed:', error);
  }
}

// Check backend health when page loads
document.addEventListener('DOMContentLoaded', checkBackendHealth);
