
#with firebse integration 

from flask import Flask, request, jsonify, render_template
from utils import get_face_embedding
from hardware import show_label_on_oled, buzz_for
import pickle, numpy as np, os, threading
from datetime import datetime
import requests  # ? ADDED for Firebase

app = Flask(__name__)

MODEL_PATH = "models/svm_classifier.pkl"
SAVE_DIR = "static/received_images"
os.makedirs(SAVE_DIR, exist_ok=True)

# ? Firebase config

FIREBASE_HOST = "https://smart-doorbell-05-default-rtdb.firebaseio.com"
FIREBASE_AUTH = "yScM4vW9Zxu730LlmLuuMc0JLUPGBgQbhcraJfM3"
FIREBASE_PATH = "/face_logs.json"  # ? You can change this path if needed

# Load models
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

def extract_datetime_from_filename(filename):
    try:
        dt_str = filename.replace("image_", "").replace(".jpg", "")
        return datetime.strptime(dt_str, "%Y-%m-%d_%H-%M-%S")
    except Exception:
        return None

@app.route('/')
def index():
    try:
        images = [img for img in os.listdir(SAVE_DIR) if img.endswith(".jpg")]
    except FileNotFoundError:
        images = []

    now = datetime.now()
    images_with_times = [(img, extract_datetime_from_filename(img)) for img in images]
    images_with_times = [(img, dt) for img, dt in images_with_times if dt is not None]

    if images_with_times:
        latest_image = min(images_with_times, key=lambda x: abs(x[1] - now))[0]
    else:
        latest_image = None

    current_time = now.strftime("%Y%m%d%H%M%S")
    images_sorted = sorted([img for img, dt in images_with_times], key=lambda x: extract_datetime_from_filename(x), reverse=True)

    return render_template("index.html", images=images_sorted, latest_image=latest_image, current_time=current_time)

@app.route('/upload', methods=['POST'])
def upload_image():
    if not request.data:
        return jsonify({"error": "No image data received"}), 400

    temp_path = "temp.jpg"
    with open(temp_path, "wb") as f:
        f.write(request.data)

    embedding = get_face_embedding(temp_path)
    if embedding is None:
        os.remove(temp_path)
        return jsonify({"error": "No face detected"}), 400

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"image_{timestamp_str}.jpg"
    final_path = os.path.join(SAVE_DIR, filename)
    os.rename(temp_path, final_path)

    probs = model.predict_proba([embedding])[0]
    confidence = max(probs)
    predicted_label = model.classes_[np.argmax(probs)]

    if confidence < 0.5:
        predicted_label = "unknown"

    print(f"?? Prediction: {predicted_label} ({round(confidence, 4)}) ? saved as {filename}")

    # ? Firebase push in a separate thread
    threading.Thread(
        target=push_to_firebase,
        args=(filename, predicted_label, round(confidence, 4), timestamp_str),
        daemon=True
    ).start()

    threading.Thread(target=run_hardware, args=(predicted_label,), daemon=True).start()

    return jsonify({
        "filename": filename,
        "label": predicted_label,
        "confidence": round(confidence, 4)
    })

def run_hardware(label):
    try:
        show_label_on_oled(label)
        buzz_for(label)
    except Exception as e:
        print(f"?? Hardware error: {e}")

# ? Push to Firebase
def push_to_firebase(filename, label, confidence, timestamp_str):
    url = f"{FIREBASE_HOST}{FIREBASE_PATH}?auth={FIREBASE_AUTH}"
    payload = {
        "filename": filename,
        "label": label,
        "confidence": confidence,
        "timestamp": timestamp_str.replace("_", " ")
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("? Firebase upload successful")
        else:
            print(f"? Firebase upload failed: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"?? Firebase exception: {e}")

if __name__ == "__main__":
    print("?? Flask Face Recognition Server Starting...")
    app.run(host="0.0.0.0", port=5000)
