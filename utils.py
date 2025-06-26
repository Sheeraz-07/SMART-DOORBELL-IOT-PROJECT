import face_recognition
import cv2
import os

def load_images_from_folder(folder_path):
    data = []
    labels = []
    for person_name in os.listdir(folder_path):
        person_folder = os.path.join(folder_path, person_name)
        if not os.path.isdir(person_folder):
            continue
        for filename in os.listdir(person_folder):
            img_path = os.path.join(person_folder, filename)
            img = cv2.imread(img_path)
            if img is None:
                continue
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb)
            encodings = face_recognition.face_encodings(rgb, boxes)
            for enc in encodings:
                data.append(enc)
                labels.append(person_name)
    return data, labels

def get_face_embedding(img_or_path):
    if isinstance(img_or_path, str) and os.path.exists(img_or_path):
        img = cv2.imread(img_or_path)
        if img is None:
            print(f"❌ Unable to load image at {img_or_path}")
            return None
    else:
        img = img_or_path  # Assume it's a raw image (NumPy array)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb)

    if len(boxes) == 0:
        print("😶 No face detected.")
        return None

    encodings = face_recognition.face_encodings(rgb, boxes)
    if len(encodings) == 0:
        print("🧠 Face found, but no encoding could be extracted.")
        return None

    return encodings[0]  # Just return the first face found
