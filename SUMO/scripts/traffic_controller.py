import traci

class SmartTrafficLight:
    def __init__(self, junction_id):
        self.junction_id = junction_id
        self.setup_traffic_light()
    
    def setup_traffic_light(self):

        existing_tls = traci.trafficlight.getIDList()
        
        if self.junction_id in existing_tls:
            print(f"Traffic light already exists at {self.junction_id}")
            self.update_program()

        else:
            print(f"Adding traffic light to {self.junction_id}")
            tl_logic = traci.trafficlight.Logic(
                programID="adaptive",
                type=0,
                currentPhaseIndex=0,
                phases=[
                    traci.trafficlight.Phase(30, "GGGrrrGGGrrr"),
                    traci.trafficlight.Phase(5,  "yyyrrryyyrrr"),
                    traci.trafficlight.Phase(30, "rrrGGGrrrGGG"),
                    traci.trafficlight.Phase(5,  "rrryyyrrryyy"),
                ]
            )
            traci.trafficlight.setProgramLogic(self.junction_id, tl_logic)
    
    def update_program(self):
        """Update traffic light program"""
        traci.trafficlight.setProgram(self.junction_id, "adaptive")
    
    def get_waiting_vehicles(self):
        """Count waiting vehicles per approach"""
        lanes = traci.trafficlight.getControlledLanes(self.junction_id)
        waiting = {}
        
        for lane in lanes:
            waiting_count = traci.lane.getLastStepHaltingNumber(lane)
            if "north" in lane or "N" in lane:
                waiting["north"] = waiting.get("north", 0) + waiting_count
            elif "south" in lane or "S" in lane:
                waiting["south"] = waiting.get("south", 0) + waiting_count
            elif "east" in lane or "E" in lane:
                waiting["east"] = waiting.get("east", 0) + waiting_count
            elif "west" in lane or "W" in lane:
                waiting["west"] = waiting.get("west", 0) + waiting_count
        
        return waiting
    
    def adapt_timing(self):
        """Dynamically adjust green time based on traffic"""
        waiting = self.get_waiting_vehicles()
        
        ns_waiting = waiting.get("north", 0) + waiting.get("south", 0)
        ew_waiting = waiting.get("east", 0) + waiting.get("west", 0)
        
        current_phase = traci.trafficlight.getPhase(self.junction_id)
        remaining = traci.trafficlight.getPhaseDuration(self.junction_id)
        
        if current_phase == 0:  
            if ns_waiting > ew_waiting * 1.5 and remaining < 10:
                traci.trafficlight.setPhaseDuration(self.junction_id, remaining + 10)
                print(f"Extended NS green at {self.junction_id}")
        
        elif current_phase == 2:
            if ew_waiting > ns_waiting * 1.5 and remaining < 10:
                traci.trafficlight.setPhaseDuration(self.junction_id, remaining + 10)
                print(f"Extended EW green at {self.junction_id}")

def run_simulation():

    traci.start(["sumo-gui", "-c", "/home/akshit/Desktop/SUMO/config/run.sumocfg"])
    
    junctions = traci.junction.getIDList()
    print(f"Found junctions: {junctions[:5]}...")
    
    target_junction = junctions[0] if junctions else ""
    
    if not target_junction:
        print("No junctions found!")
        return
    
    smart_tl = SmartTrafficLight(target_junction)
    
    step = 0
    while step < 3600:
        traci.simulationStep()
        
        if step % 5 == 0:
            smart_tl.adapt_timing()
        
        for veh_id in traci.vehicle.getIDList():
            if "emergency" in veh_id.lower() or "ambulance" in veh_id:
                pass
        
        step += 1
    
    traci.close()

if __name__ == "__main__":
    run_simulation()