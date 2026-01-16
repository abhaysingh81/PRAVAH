import traci
import time

traci.start(["sumo-gui", "-c", "config/run.sumocfg"])

step = 0
while step < 3600:
    traci.simulationStep()
    
    tl_ids = traci.trafficlight.getIDList()
    
    for tl_id in tl_ids:
        vehicles_waiting = 0
        
        controlled_lanes = traci.trafficlight.getControlledLanes(tl_id)
        for lane in controlled_lanes:
            vehicles_waiting += traci.lane.getLastStepHaltingNumber(lane)
        
        if vehicles_waiting > 5:
            current_phase = traci.trafficlight.getPhase(tl_id)
            traci.trafficlight.setPhaseDuration(tl_id, 10)
    
    step += 1

traci.close()
