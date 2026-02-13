import numpy as np

def calculate_typo_distance(s1: str, s2: str) -> int:
    """
    Optimized Levenshtein distance algorithm using NumPy for memory-efficient matrix operations.
    Useful for detecting consistent typos in suspect logs.
    """
    size_x = len(s1) + 1
    size_y = len(s2) + 1
    matrix = np.zeros ((size_x, size_y), dtype=int)
    for x in range(size_x):
        matrix [x, 0] = x
    for y in range(size_y):
        matrix [0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if s1[x-1] == s2[y-1]:
                matrix [x,y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1],
                    matrix[x, y-1] + 1
                )
            else:
                matrix [x,y] = min(
                    matrix[x-1,y] + 1,
                    matrix[x-1,y-1] + 1,
                    matrix[x,y-1] + 1
                )
    return int(matrix[size_x - 1, size_y - 1])
