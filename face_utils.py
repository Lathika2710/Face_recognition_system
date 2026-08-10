"""
face_utils.py
Wraps all face-detection / face-recognition / encoding logic so the
rest of the app never has to touch OpenCV or face_recognition directly.

Uses the `face_recognition` library (built on dlib) for encodings, and
OpenCV only for image decoding / resizing. If face_recognition is not
installed, a clear error is raised the first time it is needed rather
than at import time — see README for installation notes on dlib.
"""

import base64
import io
import os
import time
import numpy as np
import cv2

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False


class FaceEngineUnavailable(Exception):
    pass


def _require_engine():
    if not FACE_RECOGNITION_AVAILABLE:
        raise FaceEngineUnavailable(
            "The 'face_recognition' library (and its dlib dependency) is not "
            "installed. Install it to enable face detection/recognition — "
            "see README.md for platform-specific instructions."
        )


def decode_base64_image(data_url):
    """Convert a 'data:image/jpeg;base64,....' string into a BGR numpy image."""
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    img_bytes = base64.b64decode(data_url)
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img_bgr


def resize_for_processing(image_bgr, max_width=480):
    """Downscale large frames before running detection, for performance."""
    h, w = image_bgr.shape[:2]
    if w <= max_width:
        return image_bgr, 1.0
    scale = max_width / float(w)
    resized = cv2.resize(image_bgr, (max_width, int(h * scale)))
    return resized, scale


def detect_faces_and_encodings(image_bgr, upsample=1):
    """
    Detect faces in a BGR image and return a list of dicts:
    { 'box': (top, right, bottom, left), 'encoding': np.array(128,) }
    """
    _require_engine()
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb, number_of_times_to_upsample=upsample, model="hog")
    encodings = face_recognition.face_encodings(rgb, boxes)
    results = []
    for box, enc in zip(boxes, encodings):
        results.append({"box": box, "encoding": enc})
    return results


def face_quality_score(image_bgr, box):
    """
    A lightweight heuristic 'quality' score (0-100) based on sharpness
    (variance of Laplacian) and face size relative to frame — good enough
    to guide the user during capture without needing a trained model.
    """
    top, right, bottom, left = box
    h, w = image_bgr.shape[:2]
    top, left = max(0, top), max(0, left)
    bottom, right = min(h, bottom), min(w, right)
    crop = image_bgr[top:bottom, left:right]
    if crop.size == 0:
        return 0.0

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    sharpness_score = min(sharpness / 150.0, 1.0)  # normalize, cap at 1

    face_area = (bottom - top) * (right - left)
    frame_area = h * w
    size_ratio = face_area / float(frame_area)
    size_score = min(size_ratio / 0.15, 1.0)  # ideal face fills ~15%+ of frame

    brightness = float(np.mean(gray)) / 255.0
    brightness_score = 1.0 - abs(brightness - 0.5) * 2  # best around mid brightness
    brightness_score = max(0.0, brightness_score)

    quality = (sharpness_score * 0.5 + size_score * 0.3 + brightness_score * 0.2) * 100
    return round(quality, 1)


def encoding_to_blob(encoding):
    return np.asarray(encoding, dtype=np.float64).tobytes()


def blob_to_encoding(blob):
    return np.frombuffer(blob, dtype=np.float64)


def compare_encoding_to_known(unknown_encoding, known_encodings):
    """
    known_encodings: list of (person_id, name, np.array)
    Returns (best_person_id, best_name, best_confidence_percent, best_distance)
    or (None, None, 0, 1.0) if there are no known encodings.
    """
    _require_engine()
    if not known_encodings:
        return None, None, 0.0, 1.0

    arrays = np.array([k[2] for k in known_encodings])
    distances = face_recognition.face_distance(arrays, unknown_encoding)
    best_idx = int(np.argmin(distances))
    best_distance = float(distances[best_idx])
    # Convert distance (lower = better, ~0 to ~1) into an intuitive confidence %
    confidence = max(0.0, (1.0 - best_distance)) * 100
    person_id, name, _ = known_encodings[best_idx]
    return person_id, name, round(confidence, 1), best_distance


def save_snapshot(image_bgr, folder, prefix="snap"):
    os.makedirs(folder, exist_ok=True)
    filename = f"{prefix}_{int(time.time() * 1000)}.jpg"
    path = os.path.join(folder, filename)
    cv2.imwrite(path, image_bgr)
    return path


def draw_box_label(image_bgr, box, label, color=(0, 200, 0)):
    top, right, bottom, left = box
    cv2.rectangle(image_bgr, (left, top), (right, bottom), color, 2)
    cv2.rectangle(image_bgr, (left, bottom - 20), (right, bottom), color, cv2.FILLED)
    cv2.putText(image_bgr, label, (left + 4, bottom - 5), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
    return image_bgr
