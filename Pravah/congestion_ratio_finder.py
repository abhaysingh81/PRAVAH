def congestion_ratio(current_speed, free_flow_speed):
    c = 1 - (current_speed/free_flow_speed)
    return c


