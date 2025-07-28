def get_lowest_ranked_vehicle(ranking_all):
    """
    Returns the vehicle with the lowest ranking.
    
    Parameters:
        ranking_all (dict): A dictionary with keys as vehicle numbers and values as rankings.
        
    Returns:
        The key (vehicle number) corresponding to the lowest ranking.
        If the dictionary is empty, returns None.
    """
    if not ranking_all:
        return None

    return min(ranking_all, key=ranking_all.get)