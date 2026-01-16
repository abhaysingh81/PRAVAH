def line_definer(f30, f0):

    slope = (f30-f0)/30
    f10 = (slope) * 10 + f0
    f20 = (slope) * 20 + f0
    return f10, f20


