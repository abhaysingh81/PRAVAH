upstream_segments = []
alpha = 0

def num_reverser(x):
    if x != 0:
        return 1/x
    else:
        return 0
    
segments_updated = [num_reverser(x) for x in upstream_segments]

harmonic_sum = sum(segments_updated)
try:
    beta = 1/harmonic_sum
except ZeroDivisionError:
    print("NO SEGMENTS FOUND")

for i in range(len(upstream_segments)):
    alpha += (beta/i+1)*upstream_segments[i]








    
