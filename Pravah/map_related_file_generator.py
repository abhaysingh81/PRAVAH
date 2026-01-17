import pandas as pd
import json

# ===================== CONFIG =====================

SEED_POINTS_CSV = "pravah_seed_points.csv"
TRAFFIC_CSV = "pravah_900to1000_balanced.csv"
OUTPUT_JS = "data.js"

# ===================== LOAD DATA =====================

seed_df = pd.read_csv(SEED_POINTS_CSV)
traffic_df = pd.read_csv(TRAFFIC_CSV)

# Standardize column names (safe-guard)
seed_df.columns = seed_df.columns.str.lower()
traffic_df.columns = traffic_df.columns.str.lower()

# Expected columns:
# seed_df: segment_id, latitude, longitude
# traffic_df: segment_id, p50, p90

# ===================== JOIN =====================

df = seed_df.merge(
    traffic_df,
    on="segment_id",
    how="inner"
)

# ===================== GROUP BY SEGMENT =====================

segments = []

for segment_id, group in df.groupby("segment_id"):
    coords = group[["lon", "lat"]].drop_duplicates().values.tolist()

    avg_speed = group["p50"].mean()
    free_flow = group["p90"].mean()

    anomaly = avg_speed < 0.4 * free_flow
    congestion = avg_speed < 0.6 * free_flow

    segments.append({
        "id": str(segment_id),
        "coords": coords,
        "avgSpeed": round(avg_speed, 2),
        "freeFlow": round(free_flow, 2),
        "anomaly": anomaly,
        "congestion": congestion
    })

# ===================== EXPORT JS =====================

with open(OUTPUT_JS, "w", encoding="utf-8") as f:
    f.write("// AUTO-GENERATED FILE — DO NOT EDIT\n")
    f.write("// Generated from seed points + traffic analytics\n\n")
    f.write("export const segments = ")
    json.dump(segments, f, indent=2)
    f.write("\n\n")

    f.write("export const anomalySegments = segments.filter(s => s.anomaly);\n")
    f.write("export const congestedSegments = segments.filter(s => s.congestion);\n")
    f.write("""
export const cityStats = {
  avgSpeed: segments.reduce((a, b) => a + b.avgSpeed, 0) / segments.length,
  anomalyCount: anomalySegments.length,
  congestionCount: congestedSegments.length,
  totalSegments: segments.length
};
""")

print(f"✅ data.js generated with {len(segments)} segments")
