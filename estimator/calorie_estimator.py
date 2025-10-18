# estimator/calorie_estimator.py
import os
import csv

# Simple nutrition lookup via labels.csv (name -> kcal_per_100g)
LABELS_CSV = os.path.join("data", "labels.csv")

def _load_local_table():
    table = {}
    if not os.path.exists(LABELS_CSV):
        return table
    with open(LABELS_CSV, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            name = row.get("label") or row.get("name")
            kcal = row.get("kcal_per_100g")
            try:
                kcal_f = float(kcal)
            except:
                kcal_f = None
            if name:
                table[name.lower()] = kcal_f
    return table

_LOCAL_TABLE = _load_local_table()

def _nutritionix_lookup(label):
    """
    Optional: implement Nutritionix/Edamam here for better results.
    For now this is a stub returning None.
    """
    return None

def estimate_calories_for_items(detections, default_portion_g=150):
    """
    detections: list of {"label":..., "confidence":...}
    returns list with added "calories" (float) and "source"
    """
    out = []
    for d in detections:
        label = d.get("label", "").lower()
        nut = _nutritionix_lookup(label)
        if nut and "calories" in nut:
            calories = float(nut["calories"])
            source = "nutritionix"
        else:
            kcal_per_100 = _LOCAL_TABLE.get(label)
            if kcal_per_100:
                calories = round(kcal_per_100 * default_portion_g / 100.0, 1)
                source = "local_estimate"
            else:
                calories = None
                source = "unknown"

        item = {
            "label": d.get("label"),
            "confidence": d.get("confidence"),
            "calories": calories,
            "source": source,
            "bbox": d.get("bbox")
        }
        out.append(item)
    return out
