"""
backend/model.py
Incident detection using YOLOv11x — the latest Ultralytics YOLO (2024).

YOLOv11 supersedes YOLOv8 with improved accuracy and lower latency.
The 'x' (extra-large) variant gives the highest detection accuracy.

Install: pip install ultralytics
"""

from ultralytics import YOLO
import os

# ── Model path ────────────────────────────────────────────────────────────────
# Uses YOLOv11x — latest and most accurate Ultralytics model
# Set YOLO_MODEL_PATH env var to use your own custom-trained weights
MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolo11x.pt")

# ── Incident label mapping ────────────────────────────────────────────────────
# Maps COCO class names → smart city incident categories
INCIDENT_MAP = {
    "fire":        "Fire",
    "smoke":       "Fire",
    "flame":       "Fire",
    "car":         "Road Accident",
    "truck":       "Road Accident",
    "motorcycle":  "Road Accident",
    "bus":         "Road Accident",
    "bicycle":     "Road Accident",
    "crash":       "Road Accident",
    "flood":       "Flood",
    "water":       "Flood",
    "inundation":  "Flood",
    "fight":       "Public Disturbance",
    "person":      "Public Disturbance",
    "crowd":       "Public Disturbance",
    "pothole":     "Road Damage",
    "road damage": "Road Damage",
    "crack":       "Road Damage",
    "garbage":     "Illegal Dumping",
    "trash":       "Illegal Dumping",
    "waste":       "Illegal Dumping",
    "litter":      "Illegal Dumping",
}

_model = None

def _get_model():
    global _model
    if _model is None:
        print(f"[model] Loading YOLOv11x from: {MODEL_PATH}")
        _model = YOLO(MODEL_PATH)
        print(f"[model] YOLOv11x ready — {len(_model.names)} classes loaded")
    return _model


def detect_incident(file_path: str) -> dict:
    """
    Run YOLOv11x inference on an image or video file.

    Returns:
        {
            "type":        str,    # Incident category
            "confidence":  float,  # Detection confidence 0.0–1.0
            "raw_label":   str,    # Raw YOLO class label
            "all_detections": list # All boxes detected (for frontend display)
        }
    """
    model = _get_model()
    ext   = os.path.splitext(file_path)[1].lower()

    try:
        if ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
            # ── Video: sample first 10 frames ────────────────────────────────
            results    = model.predict(source=file_path, stream=True,
                                       conf=0.25, verbose=False)
            detections = []
            for i, r in enumerate(results):
                if i >= 10:
                    break
                for box in r.boxes:
                    label = model.names[int(box.cls)]
                    conf  = float(box.conf)
                    detections.append({"label": label, "confidence": conf})

            if not detections:
                return _empty_result()

            best = max(detections, key=lambda x: x["confidence"])
            best_label = best["label"]
            best_conf  = best["confidence"]
            all_dets   = detections

        else:
            # ── Image ─────────────────────────────────────────────────────────
            results = model.predict(source=file_path, conf=0.25, verbose=False)
            boxes   = results[0].boxes

            if not boxes or len(boxes) == 0:
                return _empty_result()

            all_dets = []
            for box in boxes:
                label = model.names[int(box.cls)]
                conf  = float(box.conf)
                all_dets.append({"label": label, "confidence": round(conf, 3)})

            # Sort by confidence descending
            all_dets.sort(key=lambda x: x["confidence"], reverse=True)

            best_label = all_dets[0]["label"]
            best_conf  = all_dets[0]["confidence"]

        incident_type = _map_to_incident(best_label)

        # Build clean detections list with incident mapping for frontend
        frontend_detections = []
        for d in all_dets[:5]:   # top 5 only
            frontend_detections.append({
                "raw_label":     d["label"],
                "incident_type": _map_to_incident(d["label"]),
                "confidence":    round(d["confidence"] * 100, 1),  # as %
            })

        print(f"[model] YOLOv11x → {best_label} ({best_conf:.2f}) → {incident_type}")

        return {
            "type":             incident_type,
            "confidence":       round(best_conf, 3),
            "raw_label":        best_label,
            "all_detections":   frontend_detections,
            "model_version":    "YOLOv11x",
        }

    except Exception as e:
        print(f"[model] Inference error: {e}")
        return _empty_result()


def _map_to_incident(label: str) -> str:
    lower = label.lower().strip()
    for key, incident in INCIDENT_MAP.items():
        if key in lower:
            return incident
    return label.capitalize()


def _empty_result() -> dict:
    return {
        "type":           "Unknown",
        "confidence":     0.0,
        "raw_label":      "none",
        "all_detections": [],
        "model_version":  "YOLOv11x",
    }