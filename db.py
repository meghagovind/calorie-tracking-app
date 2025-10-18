# db.py
import sqlite3
import os
import json
from datetime import datetime, timezone

DB_PATH = os.path.join("data", "meals.db")
os.makedirs("data", exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        items_json TEXT NOT NULL,
        total_cal REAL,
        note TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_meal(items, total_cal, note=None, timestamp=None):
    """
    items: list of dicts (label, confidence, calories, source, bbox)
    total_cal: float
    note: optional string (e.g., 'lunch')
    timestamp: ISO string (UTC). If None, uses now UTC.
    """
    init_db()
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO meals (timestamp, items_json, total_cal, note) VALUES (?, ?, ?, ?)",
        (timestamp, json.dumps(items, ensure_ascii=False), total_cal, note)
    )
    conn.commit()
    meal_id = cur.lastrowid
    conn.close()
    return meal_id

def get_meals_for_day(date_str):
    """
    date_str: 'YYYY-MM-DD' in local or UTC perspective; stored timestamps are ISO UTC strings.
    Returns list of meals for the given date (UTC date).
    """
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    # match by date prefix of timestamp
    prefix = date_str
    cur.execute("SELECT * FROM meals WHERE substr(timestamp,1,10) = ? ORDER BY timestamp ASC", (prefix,))
    rows = cur.fetchall()
    conn.close()
    meals = []
    for r in rows:
        meals.append({
            "id": r["id"],
            "timestamp": r["timestamp"],
            "items": json.loads(r["items_json"]),
            "total_cal": r["total_cal"],
            "note": r["note"]
        })
    return meals

def get_daily_summary(date_str):
    """
    Returns {"date": date_str, "total_cal": float, "meals_count": int, "meals": [...]}
    """
    meals = get_meals_for_day(date_str)
    total = sum([m["total_cal"] or 0 for m in meals])
    return {"date": date_str, "total_cal": total, "meals_count": len(meals), "meals": meals}
