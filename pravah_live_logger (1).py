import requests
import csv
import time
from datetime import datetime
import pytz

API_KEY = "IMyOEaUHsuhkcvq6031FhMnabunwLOzk"
URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

IST = pytz.timezone("Asia/Kolkata")

SEEDS_FILE = "pravah_seed_points.csv"
OUT = "pravah_live_from_historical_segments.csv"

# Load seeds
seeds = []
with open(SEEDS_FILE) as f:
    reader = csv.DictReader(f)
    for r in reader:
        seeds.append(r)

with open(OUT, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "timestamp_ist",
        "segment_id",
        "lat",
        "lon",
        "current_speed",
        "free_flow_speed",
        "current_travel_time",
        "free_flow_travel_time",
        "confidence",
        "road_closure"
    ])

print("Logging live traffic on PRAVAH historical segments")

while True:
    for s in seeds:
        try:
            point = f"{s['lat']},{s['lon']}"
            r = requests.get(URL, params={"point":point,"key":API_KEY}, timeout=10)
            data = r.json()

            if "flowSegmentData" not in data:
                continue

            fdata = data["flowSegmentData"]

            ts = datetime.now(IST).isoformat()

            row = [
                ts,
                s["segment_id"],
                s["lat"],
                s["lon"],
                fdata["currentSpeed"],
                fdata["freeFlowSpeed"],
                fdata["currentTravelTime"],
                fdata["freeFlowTravelTime"],
                fdata["confidence"],
                fdata["roadClosure"]
            ]

            with open(OUT, "a", newline="") as f:
                csv.writer(f).writerow(row)

            print(f"{s['segment_id']} | {fdata['currentSpeed']} km/h | conf {round(fdata['confidence'],2)}")

        except Exception as e:
            print("Error:", e)

    time.sleep(30)