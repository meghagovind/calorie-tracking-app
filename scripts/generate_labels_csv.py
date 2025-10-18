# scripts/generate_labels_csv.py
import os
import requests
import csv
import json
from dotenv import load_dotenv

load_dotenv()

ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
PROJECT_NAME = os.getenv("ROBOFLOW_PROJECT", "calorie-detection-iweay-lnwnq")
WORKSPACE = os.getenv("ROBOFLOW_WORKSPACE", "myworkspace-p5lij")
OUTPUT_FILE = os.path.join("data", "labels.csv")

if not ROBOFLOW_API_KEY:
    raise SystemExit("⚠️ Set ROBOFLOW_API_KEY in .env or environment before running.")

url = f"https://api.roboflow.com/{WORKSPACE}/{PROJECT_NAME}?api_key={ROBOFLOW_API_KEY}"
print("Fetching:", url)

resp = requests.get(url, timeout=20)
print("HTTP status:", resp.status_code)
try:
    data = resp.json()
except Exception:
    print("Response was not JSON. Raw text:")
    print(resp.text)
    raise SystemExit(1)

# quick helper to collect labels from likely places
labels_found = []

# 1) Top-level 'classes' key as list or dict
if "classes" in data:
    c = data["classes"]
    if isinstance(c, list) and all(isinstance(x, str) for x in c):
        labels_found = c
    elif isinstance(c, dict):
        # case like your JSON: keys are label names, values are counts
        labels_found = list(c.keys())

# 2) project.classes (nested)
if not labels_found and isinstance(data.get("project"), dict):
    proj = data["project"]
    if "classes" in proj:
        c = proj["classes"]
        if isinstance(c, list) and all(isinstance(x, str) for x in c):
            labels_found = c
        elif isinstance(c, dict):
            labels_found = list(c.keys())

# 3) versions -> find classes in versions entries
if not labels_found and "versions" in data:
    for v in data["versions"]:
        if isinstance(v, dict):
            # version might have 'classes' as dict or list
            if "classes" in v:
                c = v["classes"]
                if isinstance(c, list) and all(isinstance(x, str) for x in c):
                    labels_found = c
                    break
                elif isinstance(c, dict):
                    labels_found = list(c.keys())
                    break
            # sometimes version contains 'labels' or 'names'
            for key in ("labels", "names", "class_names"):
                if key in v:
                    kv = v[key]
                    if isinstance(kv, list) and all(isinstance(x, str) for x in kv):
                        labels_found = kv
                        break
        if labels_found:
            break

# If still not found, attempt a deeper recursive search for dict-of-strings keys
def search_for_label_keys(obj):
    if isinstance(obj, dict):
        # if dict where keys look like label names and values are ints or dicts -> assume keys are labels
        candidate_keys = []
        for k, v in obj.items():
            if isinstance(v, (int, float, dict)):
                candidate_keys.append(k)
        # heuristics: require at least 3 keys to reduce false matches
        if len(candidate_keys) >= 3:
            return candidate_keys
        for v in obj.values():
            res = search_for_label_keys(v)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = search_for_label_keys(item)
            if res:
                return res
    return None

if not labels_found:
    res = search_for_label_keys(data)
    if res:
        labels_found = res

if not labels_found:
    # fallback: pretty print truncated JSON for manual inspection
    print("\nCould not detect label list automatically. JSON preview (truncated):\n")
    print(json.dumps(data, indent=2)[:2000])
    raise RuntimeError("No classes/labels found automatically. Inspect the printed JSON above.")

# Clean labels: strip whitespace but preserve original casing and characters
labels = [lbl.strip() for lbl in labels_found if isinstance(lbl, str) and lbl.strip()]

print(f"\n✅ Found {len(labels)} labels. Example: {labels[:10]}")

# Write CSV
os.makedirs("data", exist_ok=True)
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as fh:
    writer = csv.writer(fh)
    writer.writerow(["label", "kcal_per_100g"])
    for label in labels:
        writer.writerow([label, ""])  # leave kcal empty for you to fill

print(f"\n✅ Saved {len(labels)} labels to {OUTPUT_FILE}")
print("Now edit data/labels.csv to add kcal_per_100g values (per 100g).")
