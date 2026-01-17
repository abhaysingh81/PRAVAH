import traci
import sumolib
import numpy as np
from shapely.geometry import LineString, Point
import pandas as pd
from datetime import datetime
import json
import math
import folium


class GPSMapper:
    def __init__(self, network_file, tomtom_data_file):

        self.net = sumolib.net.readNet(network_file)
        self.edges = self.net.getEdges()
        
        self.tomtom_data = self.load_tomtom_data(tomtom_data_file)
        
        self.edge_shapes = self.prepare_edge_shapes()
        
        self.mapping = {}
        self.unmapped_segments = []
        
    def load_tomtom_data(self, filepath):
        if filepath.endswith('.json'):
            with open(filepath, 'r') as f:
                data = json.load(f)
            return pd.json_normalize(data['segments'])
        elif filepath.endswith('.csv'):
            return pd.read_csv(filepath)
        else:
            raise ValueError("Unsupported file format. Use JSON or CSV.")
    
    def prepare_edge_shapes(self):

        edge_shapes = {}
        
        for edge in self.edges:
            edge_id = edge.getID()
            shape = edge.getShape()
            
            if len(shape) >= 2:
                line = LineString([(x, y) for x, y in shape])
                edge_shapes[edge_id] = {
                    'linestring': line,
                    'length': edge.getLength(),
                    'shape': shape
                }
        
        print(f"   Prepared {len(edge_shapes)} edge geometries")
        return edge_shapes
    
    def haversine_distance(self, coord1, coord2):

        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371000
        return c * r
    
    def convert_sumo_to_gps(self, x, y):
        return (y, x)
        
    def find_closest_edge(self, segment_coords, segment_id=""):

        best_match = None
        best_distance = float('inf')
        best_edge_id = None
        
        if len(segment_coords) < 2:
            return None
            
        segment_line = LineString(segment_coords)
        
        segment_bounds = segment_line.bounds
        buffer_distance = 0.001
        
        for edge_id, edge_data in self.edge_shapes.items():
            edge_line = edge_data['linestring']
            edge_bounds = edge_line.bounds
            
            if (edge_bounds[0] > segment_bounds[2] + buffer_distance or
                edge_bounds[2] < segment_bounds[0] - buffer_distance or
                edge_bounds[1] > segment_bounds[3] + buffer_distance or
                edge_bounds[3] < segment_bounds[1] - buffer_distance):
                continue
            
            distance = segment_line.distance(edge_line)
            
            if distance < best_distance:
                best_distance = distance
                best_edge_id = edge_id
                best_match = edge_data
        
        if best_distance < 50:
            return best_edge_id, best_distance
        else:
            return None, best_distance
    
    def map_all_segments(self, max_distance=50):
        print(f"\n🔍 Mapping {len(self.tomtom_data)} TomTom segments...")
        
        for idx, segment in self.tomtom_data.iterrows():
            segment_id = segment.get('segmentId', f"segment_{idx}")
            
            coords = []
            
            if 'coordinates' in segment and isinstance(segment['coordinates'], list):
                for coord in segment['coordinates']:
                    if isinstance(coord, dict):
                        coords.append((coord['lon'], coord['lat']))
                    else:
                        coords.append((coord[1], coord[0]))
            
            elif 'geometry.coordinates' in segment:
                try:
                    coords_data = json.loads(segment['geometry.coordinates'])
                    for coord in coords_data:
                        coords.append((coord[0], coord[1]))
                except:
                    pass
            
            elif all(k in segment for k in ['start_lat', 'start_lon', 'end_lat', 'end_lon']):
                coords = [
                    (segment['start_lon'], segment['start_lat']),
                    (segment['end_lon'], segment['end_lat'])
                ]
            
            if len(coords) < 2:
                print(f"   ⚠️ Segment {segment_id}: Not enough coordinates")
                self.unmapped_segments.append(segment_id)
                continue
            
            edge_id, distance = self.find_closest_edge(coords, segment_id)
            
            if edge_id:
                self.mapping[segment_id] = {
                    'sumo_edge': edge_id,
                    'distance_m': distance,
                    'segment_length': LineString(coords).length,
                    'tomtom_speed': segment.get('currentSpeed', 50),
                    'coordinates': coords
                }
                print(f"   ✅ {segment_id} → {edge_id} (distance: {distance:.1f}m)")
            else:
                self.unmapped_segments.append(segment_id)
                print(f"   ❌ {segment_id}: No edge found within {max_distance}m (closest: {distance:.1f}m)")
        
        print(f"\n📊 Mapping Summary:")
        print(f"   Mapped: {len(self.mapping)} segments")
        print(f"   Unmapped: {len(self.unmapped_segments)} segments")
        print(f"   Success rate: {len(self.mapping)/len(self.tomtom_data)*100:.1f}%")
        
        return self.mapping
    
    def visualize_mapping(self, output_file="mapping_visualization.html"):
        """Create interactive visualization of the mapping"""
        
        print(f"\n🎨 Creating visualization: {output_file}")
        
        all_coords = []
        for edge_data in self.edge_shapes.values():
            all_coords.extend(edge_data['shape'])
        
        if not all_coords:
            print("   ⚠️ No coordinates for visualization")
            return
        
        center_lat = all_coords[0][1]
        center_lon = all_coords[0][0]
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
        
        for edge_id, edge_data in self.edge_shapes.items():
            coords = [(y, x) for x, y in edge_data['shape']]
            folium.PolyLine(
                coords,
                color='blue',
                weight=2,
                opacity=0.7,
                popup=f"Edge: {edge_id}"
            ).add_to(m)
        
        for segment_id, mapping in self.mapping.items():
            coords = [(lat, lon) for lon, lat in mapping['coordinates']]
            folium.PolyLine(
                coords,
                color='green',
                weight=3,
                opacity=0.9,
                popup=f"TomTom: {segment_id} → SUMO: {mapping['sumo_edge']}"
            ).add_to(m)
        
        for segment_id in self.unmapped_segments[:10]:  # Limit to first 10
            segment = self.tomtom_data[self.tomtom_data['segmentId'] == segment_id]
            if not segment.empty:
                pass
        
        m.save(output_file)
        print(f"   ✅ Visualization saved to {output_file}")
        print(f"   Open in browser to see mapping results")
    
    def save_mapping(self, output_file="segment_mapping.csv"):
        """Save mapping results to CSV"""
        mapping_list = []
        
        for segment_id, data in self.mapping.items():
            mapping_list.append({
                'tomtom_segment_id': segment_id,
                'sumo_edge_id': data['sumo_edge'],
                'distance_m': data['distance_m'],
                'segment_length_m': data['segment_length'],
                'tomtom_speed_kmh': data['tomtom_speed'],
                'confidence': 'high' if data['distance_m'] < 10 else 'medium'
            })
        
        df = pd.DataFrame(mapping_list)
        df.to_csv(output_file, index=False)
        print(f"\n💾 Mapping saved to {output_file}")
        
        if self.unmapped_segments:
            unmapped_df = pd.DataFrame({'unmapped_segments': self.unmapped_segments})
            unmapped_df.to_csv('unmapped_segments.csv', index=False)
            print(f"   Unmapped segments saved to unmapped_segments.csv")
        
        return df

class TomTomGPSSimulator:
    def __init__(self, network_file, tomtom_file, config_file="config/run.sumocfg"):
        self.network_file = network_file
        self.tomtom_file = tomtom_file
        self.config_file = config_file
        
        print("="*60)
        print("🚗 TOMTOM GPS-BASED TRAFFIC SIMULATION")
        print("="*60)
        
        print("\n1. Creating GPS-based mapping...")
        self.mapper = GPSMapper(network_file, tomtom_file)
        self.mapping = self.mapper.map_all_segments()
        
        self.mapper.save_mapping()
        self.mapper.visualize_mapping()
        
        self.edge_speeds = self.prepare_speed_data()
    
    def prepare_speed_data(self):
        edge_speeds = {}
        
        for segment_id, mapping in self.mapping.items():
            edge_id = mapping['sumo_edge']
            
            segment_data = self.mapper.tomtom_data[
                self.mapper.tomtom_data['segmentId'] == segment_id
            ]
            
            if not segment_data.empty:
                speed = segment_data.iloc[0].get('currentSpeed', 50)
                timestamp = segment_data.iloc[0].get('timestamp', '08:00')
                
                sim_time = self.time_to_seconds(timestamp)
                
                if edge_id not in edge_speeds:
                    edge_speeds[edge_id] = []
                
                edge_speeds[edge_id].append({
                    'time': sim_time,
                    'speed_kmh': speed,
                    'segment_id': segment_id
                })
        
        for edge_id in edge_speeds:
            edge_speeds[edge_id].sort(key=lambda x: x['time'])
        
        return edge_speeds
    
    def time_to_seconds(self, time_str):
        try:
            if 'T' in time_str:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                return dt.hour * 3600 + dt.minute * 60 + dt.second
            else:
                hours, minutes = map(int, time_str.split(':'))
                return hours * 3600 + minutes * 60
        except:
            return 0
    
    def run_simulation(self):
        print("\n2. Starting SUMO simulation with TomTom speeds...")
        
        traci.start(["sumo-gui", "-c", self.config_file])
        
        all_edges = traci.edge.getIDList()
        
        step = 0
        last_update = 0
        
        while traci.simulation.getMinExpectedNumber() > 0 and step < 86400:  # Max 24 hours
            traci.simulationStep()
            
            if step - last_update >= 30:
                self.update_edge_speeds(step)
                last_update = step
            
            if step % 60 == 0:
                self.monitor_congestion(step)
            
            step += 1
        
        traci.close()
        print("\n✅ Simulation complete!")
    
    def update_edge_speeds(self, sim_time):
        updates = 0
        
        for edge_id, speed_data in self.edge_speeds.items():
            closest = None
            min_diff = float('inf')
            
            for data_point in speed_data:
                time_diff = abs(data_point['time'] - sim_time)
                if time_diff < min_diff:
                    min_diff = time_diff
                    closest = data_point
            
            if closest and min_diff < 1800:
                speed_kmh = closest['speed_kmh']
                speed_mps = speed_kmh * 0.27778
                
                try:
                    current_speed = traci.edge.getMaxSpeed(edge_id)
                    new_speed = current_speed * 0.8 + speed_mps * 0.2
                    traci.edge.setMaxSpeed(edge_id, new_speed)
                    updates += 1
                except:
                    pass
        
        if updates > 0:
            print(f"   Updated {updates} edges at time {sim_time}s")
    
    def monitor_congestion(self, sim_time):
        """Monitor and log congestion"""
        congested_edges = []
        
        for edge_id in self.edge_speeds.keys():
            try:
                mean_speed = traci.edge.getLastStepMeanSpeed(edge_id)
                vehicle_count = traci.edge.getLastStepVehicleNumber(edge_id)
                
                if mean_speed < 5.0 and vehicle_count > 5:
                    congested_edges.append((edge_id, mean_speed, vehicle_count))
            except:
                pass
        
        if congested_edges:
            print(f"\n⚠️  CONGESTION DETECTED at {sim_time}s:")
            for edge_id, speed, count in congested_edges:
                print(f"   {edge_id}: {speed:.1f} m/s, {count} vehicles")
    
    def generate_report(self):
        """Generate mapping and simulation report"""
        print("\n" + "="*60)
        print("📋 SIMULATION REPORT")
        print("="*60)
        
        print(f"\nMapping Statistics:")
        print(f"   Total TomTom segments: {len(self.mapper.tomtom_data)}")
        print(f"   Successfully mapped: {len(self.mapping)}")
        print(f"   Mapping rate: {len(self.mapping)/len(self.mapper.tomtom_data)*100:.1f}%")
        
        distances = [m['distance_m'] for m in self.mapping.values()]
        if distances:
            print(f"   Average mapping distance: {np.mean(distances):.1f}m")
            print(f"   Max mapping distance: {np.max(distances):.1f}m")

def quick_start():
    
    sample_data = []
    base_lat, base_lon = 28.6139, 77.2090
    
    for i in range(10):
        segment_data = {
            "segmentId": f"segment_{i}",
            "currentSpeed": np.random.uniform(20, 70),
            "freeFlowSpeed": 60,
            "timestamp": "08:00",
            "coordinates": [
                {"lat": base_lat + np.random.uniform(-0.01, 0.01),
                 "lon": base_lon + np.random.uniform(-0.01, 0.01)},
                {"lat": base_lat + np.random.uniform(-0.01, 0.01),
                 "lon": base_lon + np.random.uniform(-0.01, 0.01)}
            ]
        }
        sample_data.append(segment_data)
    
    with open('sample_tomtom_gps.json', 'w') as f:
        json.dump({"segments": sample_data}, f, indent=2)
    
    print("✅ Created sample_tomtom_gps.json")
    

requirements = """
Install these packages first:

pip install sumolib
pip install shapely
pip install pandas
pip install numpy
pip install folium  # for visualization
pip install pyproj  # for coordinate transformations

For Ubuntu/Debian:
sudo apt-get install libgeos-dev
"""

if __name__ == "__main__":
    print(requirements)
    
    quick_start()