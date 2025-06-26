import pickle
from sklearn import svm
from utils import load_images_from_folder
import os

os.makedirs("models", exist_ok=True)
os.makedirs("embeddings", exist_ok=True)

print("[INFO] Loading dataset and extracting features...")
X, y = load_images_from_folder("dataset")

print(f"[INFO] Found {len(X)} face embeddings")

print("[INFO] Training SVM classifier...")
clf = svm.SVC(kernel='linear', probability=True)
clf.fit(X, y)

with open("models/svm_classifier.pkl", "wb") as f:
    pickle.dump(clf, f)

with open("embeddings/face_embeddings.pkl", "wb") as f:
    pickle.dump((X, y), f)

print("[INFO] Training complete. Models saved!")
