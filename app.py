# app.py
import os
import datetime
from flask import Flask, render_template, request, jsonify
from detection.roboflow_client import detect_with_roboflow
from estimator.calorie_estimator import estimate_calories_for_items
import db  # the db.py file

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")


db.init_db()

DETECTION_BACKEND = os.getenv("DETECTION_BACKEND", "roboflow")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:
        return jsonify({"error": "no image uploaded"}), 400
    f = request.files["image"]
    filename = f.filename or "upload.jpg"
    saved_path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(saved_path)

    # detect
    if DETECTION_BACKEND == "yolov8":
        detections = detect_with_yolov8(saved_path)
    else:
        detections = detect_with_roboflow(saved_path)

    # estimate calories
    estimates = estimate_calories_for_items(detections)
    total = sum([it["calories"] or 0 for it in estimates])
    response = {
        "items": estimates,
        "total_estimated_calories": round(total, 2)
    }

    # if client asked to auto-save (form field 'save' = '1' or query param)
    save_flag = request.form.get("save") or request.args.get("save")
    if save_flag in ("1", "true", "yes"):
        note = request.form.get("note")
        meal_id = db.save_meal(estimates, total, note=note)
        response["saved"] = True
        response["meal_id"] = meal_id

    return jsonify(response)

@app.route("/save_meal", methods=["POST"])
def save_meal_endpoint():
    data = request.get_json(force=True)
    items = data.get("items", [])
    total = data.get("total_estimated_calories", 0)
    note = data.get("note")
    # optional timestamp support
    timestamp = data.get("timestamp")  # ISO string
    meal_id = db.save_meal(items, total, note=note, timestamp=timestamp)
    return jsonify({"saved": True, "meal_id": meal_id})

@app.route("/summary", methods=["GET"])
def summary():
    # date param in 'YYYY-MM-DD', default to today's date in UTC
    date_str = request.args.get("date")
    if not date_str:
        date_str = datetime.datetime.utcnow().date().isoformat()
    summary = db.get_daily_summary(date_str)
    return jsonify(summary)

if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True, port=5000)
