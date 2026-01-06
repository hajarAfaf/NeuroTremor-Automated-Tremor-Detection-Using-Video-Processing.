import cv2
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.fft import fft
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from datetime import datetime
import pickle
# Charger le modèle ML pour classification
MODEL_PATH = "models/tremblement_model.pkl"
ml_model = pickle.load(open(MODEL_PATH, "rb"))

# ----- FILTRE BANDE PASSANTE -----
def bandpass_filter(signal, fs, low=4, high=6, order=4):
    nyq = 0.5 * fs
    b, a = butter(order, [low/nyq, high/nyq], btype='band')
    return filtfilt(b, a, signal)
def classify_tremor(signal_features):
    """Retourne type de tremblement et score"""
    pred = ml_model.predict([signal_features])[0]
    score = np.std(signal_features) * np.max(np.abs(signal_features))
    if score < 0.002:
        severity = "Faible"
    elif score < 0.005:
        severity = "Moyen"
    else:
        severity = "Élevé"
    return pred, severity

# ----- ANALYSE VIDEO -----
def analyze_video(video_path, patient_age=60, result_dir="static/results"):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Vidéo introuvable : {video_path}")

    os.makedirs(result_dir, exist_ok=True)
    # Adapter la bande passante selon l'âge
    if patient_age < 40:
        low, high = 4.5, 6.5
    elif patient_age > 70:
        low, high = 3.5, 5.5
    else:
        low, high = 4, 6
    # Charger le modèle Mediapipe
    base_options = python.BaseOptions(model_asset_path="models/hand_landmarker.task")
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2,
        running_mode=vision.RunningMode.VIDEO
    )
    detector = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    timestamp_ms = 0
    y_positions = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb)
        result = detector.detect_for_video(mp_image, int(timestamp_ms))

        if result.hand_landmarks:
            wrist = result.hand_landmarks[0][0]
            y_positions.append(wrist.y)

        timestamp_ms += 1000 / fps

    cap.release()

    # Vérification sécurité
    if len(y_positions) < 10:
        return {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "file": os.path.basename(video_path),
            "amplitude": "Non détectée",
            "frequency": "Non détectée",
            "graph": None,
            "interpretation": "Main non détectée",
            "alert": None
        }

    # Traitement du signal
    signal = bandpass_filter(np.array(y_positions), fps)
    amplitude = float(np.std(signal))
    fft_vals = np.abs(fft(signal))
    freqs = np.fft.fftfreq(len(fft_vals), 1 / fps)
    dominant_freq = abs(freqs[np.argmax(fft_vals)])

    # Graphique
    plt.figure()
    plt.plot(signal)
    plt.title("Mouvement vertical du poignet")
    plt.xlabel("Frame")
    plt.ylabel("Position normalisée")
    graph_path = os.path.join(result_dir, f"signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    plt.savefig(graph_path)
    plt.close()
    # ML Classification
    features = signal[-100:]  # exemple simple, dernière partie du signal
    tremor_type, severity = classify_tremor(features)
    
    # Interprétation
    interpretation = "Mouvement normal"
    alert = None
    if 4 <= dominant_freq <= 6:
        interpretation = "Oscillation 4–6 Hz : tremblement pathologique possible."
        alert = "Tremblement suspect détecté"
    elif dominant_freq >= 8:
        interpretation = "Tremblement physiologique possible (stress, fatigue, froid)."

    if amplitude > 0.002:
        interpretation += " Amplitude élevée observée."

    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "file": os.path.basename(video_path),
        "amplitude": round(amplitude, 4),
        "frequency": round(dominant_freq, 2),
        "graph": "/" + graph_path.replace("\\", "/"),
        "interpretation": interpretation,
        "alert": alert
    }
