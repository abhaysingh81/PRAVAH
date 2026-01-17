def congestion_ratio(free_flow, continuous_flow):
    if continuous_flow <= 0:
        return None
    return 1.0 - (free_flow / continuous_flow)



def build_congestion_ratio_map(
    junction_mapping,
    current_speed,
    free_flow_speed
):
    result = {}

    for junction_id, sides in junction_mapping.items():
        result[junction_id] = {}

        for side, segment_ids in sides.items():
            result[junction_id][side] = {}

            for seg_id in segment_ids:
                if seg_id not in current_speed:
                    continue
                if seg_id not in free_flow_speed:
                    continue

                v = current_speed[seg_id]
                v_ff = free_flow_speed[seg_id]

                ratio = congestion_ratio(v_ff, v)
                result[junction_id][side][seg_id] = ratio

    return result
