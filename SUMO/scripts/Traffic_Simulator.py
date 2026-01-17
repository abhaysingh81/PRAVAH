import traci
import pandas as pd
import time
from datetime import datetime
import numpy as np

class TomTomTrafficSimulator:
    def __init__(self, tomtom_data_path, config_file="config/run.sumocfg"):
        """
        Initialize simulator with TomTom speed data
        
        Args:
            tomtom_data_path: Path to CSV with TomTom segment speeds
            config_file: SUMO configuration file
        """
        self.config_file = config_file
        self.tomtom_data = self.load_tomtom_data(tomtom_data_path)
        self.edge_speed_map = {}
        self.time_patterns = {}
        
        self.segment_to_edge = self.create_segment_mapping()
        
        self.stats = {
            'edge_speed_updates': 0,
            'vehicle_speed_updates': 0,
            'congestion_changes': 0
        }
    
    def load_tomtom_data(self, filepath):
        print(f"📊 Loading TomTom data from {filepath}")
        
        data = pd.read_csv(filepath)
        
        if 'timestamp' in data.columns:
            data['sim_time'] = data['timestamp'].apply(self.time_to_seconds)
        
        print(f"   Loaded {len(data)} records")
        print(f"   Time range: {data['timestamp'].min()} to {data['timestamp'].max()}")
        print(f"   Speed range: {data['avg_speed_kmh'].min()} to {data['avg_speed_kmh'].max()} km/h")
        
        return data
    
    def time_to_seconds(self, time_str):
        """Convert HH:MM time to simulation seconds"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 3600 + minutes * 60
        except:
            return 0
    
    def create_segment_mapping(self):
        mapping = {}
        
        example_mapping = {
            'segment_123': 'edge1',
            'segment_456': 'edge2',
        }
        
        print("⚠️  You need to create segment-to-edge mapping!")
        print("   Options:")
        print("   1. Manual mapping (create mapping.csv)")
        print("   2. Automatic by road name matching")
        print("   3. Automatic by geographical coordinates")
        
        return example_mapping
    
    def start_simulation(self):
        """Start SUMO simulation with TomTom data"""
        print("🚦 Starting SUMO simulation with TomTom data...")
        
        traci.start(["sumo-gui", "-c", self.config_file])
        
        self.initialize_edge_speeds()
        
        step = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            
            if step % 30 == 0:
                self.update_speeds_from_tomtom(step)
            
            if step % 5 == 0:
                self.apply_speeds_to_vehicles()
            
            if step % 60 == 0:
                self.collect_statistics(step)
            
            self.check_for_congestion(step)
            
            step += 1
        
        traci.close()
        print("✅ Simulation complete!")
        self.print_statistics()
    
    def initialize_edge_speeds(self):
        """Initialize all edge speeds from TomTom data"""
        print("📈 Initializing edge speeds...")
        
        all_edges = traci.edge.getIDList()
        
        initial_data = self.tomtom_data[self.tomtom_data['sim_time'] == 0]
        if len(initial_data) == 0:
            initial_data = self.tomtom_data.iloc[0:1]
        
        for _, row in initial_data.iterrows():
            segment_id = row['segment_id']
            speed_kmh = row['avg_speed_kmh']
            speed_mps = speed_kmh * 0.27778
            
            if segment_id in self.segment_to_edge:
                edge_id = self.segment_to_edge[segment_id]
                if edge_id in all_edges:
                    traci.edge.setMaxSpeed(edge_id, speed_mps)
                    self.edge_speed_map[edge_id] = speed_mps
                    
                    print(f"   Edge {edge_id}: {speed_kmh:.1f} km/h ({speed_mps:.1f} m/s)")
                    self.stats['edge_speed_updates'] += 1
    
    def update_speeds_from_tomtom(self, sim_time):

        current_hour = (sim_time // 3600) % 24
        
        time_window_start = current_hour * 3600 - 900
        time_window_end = current_hour * 3600 + 900
        
        time_data = self.tomtom_data[
            (self.tomtom_data['sim_time'] >= time_window_start) &
            (self.tomtom_data['sim_time'] <= time_window_end)
        ]
        
        if len(time_data) == 0:
            time_data = self.tomtom_data[
                (self.tomtom_data['sim_time'] // 3600) == current_hour
            ]
        
        for _, row in time_data.iterrows():
            segment_id = row['segment_id']
            speed_kmh = row['avg_speed_kmh']
            speed_mps = speed_kmh * 0.27778
            
            if segment_id in self.segment_to_edge:
                edge_id = self.segment_to_edge[segment_id]
                
                current_speed = self.edge_speed_map.get(edge_id, speed_mps)
                new_speed = current_speed * 0.7 + speed_mps * 0.3
                
                traci.edge.setMaxSpeed(edge_id, new_speed)
                self.edge_speed_map[edge_id] = new_speed
                
                self.stats['edge_speed_updates'] += 1
    
    def apply_speeds_to_vehicles(self):

        vehicle_ids = traci.vehicle.getIDList()
        
        for veh_id in vehicle_ids:
            try:
                road_id = traci.vehicle.getRoadID(veh_id)
                
                if road_id in self.edge_speed_map:
                    target_speed = self.edge_speed_map[road_id]
                    
                    veh_type = traci.vehicle.getTypeID(veh_id)
                    type_max_speed = traci.vehicletype.getMaxSpeed(veh_type)
                    
                    actual_speed = min(target_speed, type_max_speed)
                    
                    traci.vehicle.setSpeed(veh_id, actual_speed)
                    self.stats['vehicle_speed_updates'] += 1
                    
            except traci.exceptions.TraCIException:
                pass
    
    def check_for_congestion(self, sim_time):
        critical_edges = ['edge1', 'edge2', 'edge3']
        
        for edge_id in critical_edges:
            if edge_id in self.edge_speed_map:
                vehicle_count = traci.edge.getLastStepVehicleNumber(edge_id)
                mean_speed = traci.edge.getLastStepMeanSpeed(edge_id)
                
                if mean_speed < 5.0 and vehicle_count > 10:
                    print(f"⚠️  CONGESTION detected on {edge_id} at time {sim_time}s")
                    print(f"   Speed: {mean_speed:.1f} m/s, Vehicles: {vehicle_count}")
                    
                    self.adapt_traffic_lights_for_congestion(edge_id)
                    self.stats['congestion_changes'] += 1
    
    def adapt_traffic_lights_for_congestion(self, congested_edge):

        all_tls = traci.trafficlight.getIDList()
        
        for tl_id in all_tls:
            controlled_lanes = traci.trafficlight.getControlledLanes(tl_id)
            
            for lane in controlled_lanes:
                if congested_edge in lane:
                    print(f"   Adjusting traffic light {tl_id} for congestion")
                    
                    current_phase = traci.trafficlight.getPhase(tl_id)
                    remaining = traci.trafficlight.getPhaseDuration(tl_id)
                    
                    traci.trafficlight.setPhaseDuration(tl_id, remaining + 10)
                    break
    
    def collect_statistics(self, sim_time):
        print(f"\n📊 Statistics at {sim_time}s:")
        
        total_error = 0
        count = 0
        
        for edge_id, target_speed in self.edge_speed_map.items():
            try:
                actual_speed = traci.edge.getLastStepMeanSpeed(edge_id)
                error = abs(actual_speed - target_speed)
                total_error += error
                count += 1
                
                if error > 5.0:
                    print(f"   Edge {edge_id}: Target={target_speed:.1f}, Actual={actual_speed:.1f} (Δ={error:.1f})")
            except:
                pass
        
        if count > 0:
            avg_error = total_error / count
            print(f"   Average speed error: {avg_error:.2f} m/s")
    
    def print_statistics(self):
        print("\n" + "="*50)
        print("📈 FINAL SIMULATION STATISTICS")
        print("="*50)
        print(f"Edge speed updates: {self.stats['edge_speed_updates']}")
        print(f"Vehicle speed updates: {self.stats['vehicle_speed_updates']}")
        print(f"Congestion responses: {self.stats['congestion_changes']}")
        
        if len(self.edge_speed_map) > 0:
            print(f"\nTomTom speed compliance: {len(self.edge_speed_map)} edges controlled")

def generate_sample_tomtom_data(filename="tomtom_data.csv"):
    import random
    
    data = []
    segments = ['segment_001', 'segment_002', 'segment_003', 'segment_004']
    
    for hour in range(24):
        for minute in [0, 15, 30, 45]:
            timestamp = f"{hour:02d}:{minute:02d}"
            sim_time = hour * 3600 + minute * 60
            
            for segment in segments:
                if 7 <= hour <= 9:
                    speed = random.uniform(20, 40)
                elif 17 <= hour <= 19:
                    speed = random.uniform(25, 45)
                else:
                    speed = random.uniform(50, 70)
                
                speed += random.uniform(-5, 5)
                speed = max(10, min(80, speed))
                
                congestion = "low"
                if speed < 30:
                    congestion = "high"
                elif speed < 50:
                    congestion = "medium"
                
                data.append({
                    'segment_id': segment,
                    'road_name': f'Road_{segment[-3:]}',
                    'avg_speed_kmh': round(speed, 1),
                    'congestion_level': congestion,
                    'timestamp': timestamp
                })
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"✅ Generated sample TomTom data: {filename}")
    print(f"   {len(df)} records, {len(segments)} segments")
    
    return df


if __name__ == "__main__":
    generate_sample_tomtom_data("data/tomtom_sample.csv")
    
    mapping_data = {
        'tomtom_segment_id': ['segment_001', 'segment_002', 'segment_003', 'segment_004'],
        'sumo_edge_id': ['edge1', 'edge2', 'edge3', 'edge4'],
        'road_name': ['Main_St', 'First_Ave', 'Second_St', 'Third_Ave']
    }
    pd.DataFrame(mapping_data).to_csv('segment_mapping.csv', index=False)
    
    
    simulator = TomTomTrafficSimulator(
        tomtom_data_path="data/tomtom_sample.csv",
        config_file="config/run.sumocfg"
    )
    
    simulator.start_simulation()