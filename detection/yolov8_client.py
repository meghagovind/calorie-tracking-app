# detection/yolov8_client.py
from ultralytics import YOLO
import os

# Path to weights if you trained locally, or use yolov8n.pt
YOLO_WEIGHTS = os.getenv("YOLO_WEIGHTS", "yolov8n.pt")
_model = None

def _load_model():
    global _model
    if _model is None:
        _model = YOLO(YOLO_WEIGHTS)
    return _model

def detect_with_yolov8(image_path, conf=0.25):
    model = _load_model()
    results = model.predict(source=image_path, conf=conf, imgsz=640)
    out = []
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            name = model.model.names.get(cls, str(cls)) if hasattr(model, "model") else str(cls)
            conf_score = float(box.conf[0])
            # xyxy
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            w = x2 - x1
            h = y2 - y1
            cx = x1 + w/2
            cy = y1 + h/2
            out.append({
                "label": name,
                "confidence": conf_score,
                "bbox": {"x": cx, "y": cy, "width": w, "height": h}
            })
    return out
