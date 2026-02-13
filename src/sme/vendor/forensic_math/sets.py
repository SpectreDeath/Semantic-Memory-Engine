from typing import List, Any

def calculate_set_overlap(list1: List[Any], list2: List[Any]) -> float:
    """
    Calculates the Jaccard Similarity (Set Overlap) between two lists of tokens.
    Useful for identifying shared technical jargon between aliases.
    """
    set1 = set(list1)
    set2 = set(list2)
    
    if not set1 and not set2:
        return 1.0
        
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return float(intersection / union)
