from typing import Any


def calculate_set_overlap(list1: list[Any], list2: list[Any]) -> float:
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
