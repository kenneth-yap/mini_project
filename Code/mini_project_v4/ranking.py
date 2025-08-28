def get_lowest_ranked_vehicle(ranking_all):
    """
    Returns the vehicle with the lowest numeric ranking.
    
    ranking_all: dict
        keys = vehicle_number
        values = either numeric ranking OR tuple/list like (addr, ranking)
    
    Returns:
        vehicle_number with the lowest ranking
    """
    if not ranking_all:
        return None

    cleaned = {}
    for k, v in ranking_all.items():
        if isinstance(v, (tuple, list)):
            # v = (addr, ranking)
            cleaned[k] = v[1]  # <-- take the numeric ranking
        else:
            cleaned[k] = v

    return min(cleaned, key=cleaned.get)