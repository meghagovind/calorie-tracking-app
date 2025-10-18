# detection/roboflow_client.py
import os
import requests

ROBOFLOW_MODEL_ENDPOINT = os.getenv("ROBOFLOW_MODEL_ENDPOINT", "").rstrip("/")
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")

def detect_with_roboflow(image_path):
    """
    Returns list of detections: [{"label": str, "confidence": float, "bbox": {...}}, ...]
    """
    if not ROBOFLOW_MODEL_ENDPOINT:
        raise RuntimeError("ROBOFLOW_MODEL_ENDPOINT not set")

    url = ROBOFLOW_MODEL_ENDPOINT
    if ROBOFLOW_API_KEY:
        url = f"{url}?api_key={ROBOFLOW_API_KEY}"

    with open(image_path, "rb") as f:
        files = {"file": ("image.jpg", f, "image/jpeg")}
        r = requests.post(url, files=files, timeout=25)
        r.raise_for_status()
        data = r.json()

    preds = data.get("predictions", [])
    out = []
    for p in preds:
        out.append({
            "label": p.get("class") or p.get("label") or p.get("predicted_class"),
            "confidence": float(p.get("confidence", 0)),
            "bbox": {
                "x": p.get("x"), "y": p.get("y"),
                "width": p.get("width"), "height": p.get("height")
            }
        })
    return out
