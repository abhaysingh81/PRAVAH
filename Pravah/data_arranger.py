import pandas as pd
import geopandas as gpd
import folium
import random
from shapely import wkt

# =============================
# CONFIG
# =============================

SEGMENT_OPACITY = 0.8
SEGMENT_WEIGHT = 5

# =============================
# LOAD DATA
# =============================

# Seed points
seed_df = pd.read_csv("pravah_seed_points.csv")
seed_gdf = gpd.GeoDataFrame(
    seed_df,
    geometry=gpd.points_from_xy(seed_df.lon, seed_df.lat),
    crs="EPSG:4326"
)

# Segments with WKT geometry
segments_df = pd.read_csv("pravah_900to1000_balanced.csv")
segments_df["geometry"] = segments_df["geometry_wkt"].apply(wkt.loads)

segments_gdf = gpd.GeoDataFrame(
    segments_df,
    geometry="geometry",
    crs="EPSG:4326"
)

# Use one geometry per segment_id
segments_gdf = segments_gdf.drop_duplicates("segment_id")

# =============================
# CREATE BASE MAP
# =============================

center_lat = seed_gdf.lat.mean()
center_lon = seed_gdf.lon.mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=14,
    tiles="cartodbpositron"
)

# =============================
# COLOR GENERATOR
# =============================

def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

segment_colors = {
    seg_id: random_color()
    for seg_id in segments_gdf.segment_id.unique()
}

# =============================
# ADD SEGMENTS
# =============================

segments_fg = folium.FeatureGroup(name="Segments")

for _, row in segments_gdf.iterrows():
    seg_id = row.segment_id
    geom = row.geometry

    if geom.geom_type == "LineString":
        coords = [(lat, lon) for lon, lat in geom.coords]

        folium.PolyLine(
            locations=coords,
            color=segment_colors[seg_id],
            weight=SEGMENT_WEIGHT,
            opacity=SEGMENT_OPACITY,
            tooltip=f"Segment ID: {seg_id}",
            popup=f"Segment ID: {seg_id}"
        ).add_to(segments_fg)

segments_fg.add_to(m)

# =============================
# ADD SEED POINTS
# =============================

seeds_fg = folium.FeatureGroup(name="Seed Points")

for _, row in seed_gdf.iterrows():
    seed_id = row.get("seed_id", row.name)

    folium.CircleMarker(
        location=[row.lat, row.lon],
        radius=6,
        color="red",
        fill=True,
        fill_opacity=1.0,
        tooltip=f"Seed: {seed_id}",
        popup=f"Seed ID: {seed_id}"
    ).add_to(seeds_fg)

seeds_fg.add_to(m)

# =============================
# LAYER CONTROL
# =============================

folium.LayerControl(collapsed=False).add_to(m)

# =============================
# SAVE MAP
# =============================

output_file = "segments_visualizer.html"
m.save(output_file)

print(f"Interactive map saved as {output_file}")
