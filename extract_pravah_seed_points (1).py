import csv

INPUT = "pravah_monday_full.csv"
OUTPUT = "pravah_seed_points.csv"

def midpoint(wkt):
    coords = wkt.replace("LINESTRING(","").replace(")","").split(",")
    mid = coords[len(coords)//2]
    lon, lat = mid.strip().split(" ")
    return lat, lon

seeds = {}

with open(INPUT, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        seg = row["segment_id"]
        if seg not in seeds:
            lat, lon = midpoint(row["geometry_wkt"])
            seeds[seg] = (lat, lon)

with open(OUTPUT, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["segment_id","lat","lon"])
    for seg,(lat,lon) in seeds.items():
        writer.writerow([seg,lat,lon])

print("Created:", OUTPUT)