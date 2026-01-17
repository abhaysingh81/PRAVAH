import pandas as pd
from geopy.distance import geodesic
from csv_to_dict_maker import output_csv_file


def analyze_junction_flow(file_path, junction_lat, junction_lon, threshold_meters=100):
    """
    Identifies upstream and downstream segments for a given junction.
    
    Args:
        file_path (str): Path to the CSV file.
        junction_lat (float): Latitude of the intersection.
        junction_lon (float): Longitude of the intersection.
        threshold_meters (float): Distance tolerance to consider a point "at" the junction.
    """
    
    # 1. Load the Data
    # Assuming CSV columns: 'seed', 'lat', 'lon'
    df = pd.read_csv(file_path)
    
    # Check if data is sorted; if not, sort by index or a sequence column if you have one.
    # df = df.sort_values(by=['seed', 'sequence_id']) 
    
    # 2. Group points into Segments (Curves) based on 'seed'
    # We only need the First and Last point of every seed to determine connectivity.
    segments = df.groupby('segment_id').agg(
        start_lat=('lat', 'first'),
        start_lon=('lon', 'first'),
        end_lat=('lat', 'last'),
        end_lon=('lon', 'last'),
        point_count=('lat', 'count') # Optional: just to check data quality
    ).reset_index()

    upstream_segments = []
    downstream_segments = []
    
    target_junction = (junction_lat, junction_lon)

    print(f"Analyzing Junction: {target_junction} with {threshold_meters}m tolerance...")
    print("-" * 40)

    # 3. Iterate through every segment to check connectivity
    for index, row in segments.iterrows():
        seed_id = row['segment_id']
        
        # Define the start and end coordinates of this segment
        segment_start = (row['start_lat'], row['start_lon'])
        segment_end = (row['end_lat'], row['end_lon'])
        
        # Calculate distances to the target junction
        dist_from_start = geodesic(target_junction, segment_start).meters
        dist_from_end = geodesic(target_junction, segment_end).meters
        
        # 4. Classify the Segment
        
        # CASE A: DOWNSTREAM (The segment STARTS here and goes away)
        if dist_from_start <= threshold_meters:
            downstream_segments.append(seed_id)
            
        # CASE B: UPSTREAM (The segment ENDS here)
        if dist_from_end <= threshold_meters:
            upstream_segments.append(seed_id)

    # 5. Output Results
    print(f"Found {len(upstream_segments)} Upstream Segments (Incoming): {upstream_segments}")
    print(f"Found {len(downstream_segments)} Downstream Segments (Outgoing): {downstream_segments}")
    
    return {
        "upstream": upstream_segments,
        "downstream": downstream_segments
    }

# --- USAGE EXAMPLE ---
# Create a dummy CSV for testing
# (You can skip this block if you use your actual file)
data = output_csv_file("pravah_seed_points.csv")
# Segment 1: Ends at 12.91, 77.61 (Upstream)
# Segment 2: Starts at 12.91, 77.61 (Downstream)
# Segment 3: Starts at 12.91, 77.61 (Downstream)
pd.DataFrame(data).to_csv('traffic_data.csv', index=False)

# Run the function
# We use 12.91, 77.61 as our target junction
results = analyze_junction_flow('traffic_data.csv', 28.628180, 77.246868)