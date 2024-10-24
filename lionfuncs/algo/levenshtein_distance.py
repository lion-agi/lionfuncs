from itertools import product


def levenshtein_distance(a: str, b: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.

    The Levenshtein distance is the minimum number of single-character edits
    (insertions, deletions, or substitutions) required to change one word
    into the other.

    Args:
        a: The first string to compare.
        b: The second string to compare.

    Returns:
        The Levenshtein distance between the two strings.

    Algorithm:
        1. Initialize a 2D array with dimensions (len(a)+1) x (len(b)+1).
        2. Populate the base case values for transforming prefixes.
        3. Use dynamic programming to compute the distance by considering
           insertions, deletions, and substitutions.
        4. Return the computed distance.
    """
    m, n = len(a), len(b)

    # Initialize 2D array (m+1) x (n+1)
    d = [[0] * (n + 1) for _ in range(m + 1)]

    # Populate the base case values
    for i in range(m + 1):
        d[i][0] = i
    for j in range(n + 1):
        d[0][j] = j

    # Compute the distance
    for i, j in product(range(1, m + 1), range(1, n + 1)):
        cost = 0 if a[i - 1] == b[j - 1] else 1
        d[i][j] = min(
            d[i - 1][j] + 1,  # deletion
            d[i][j - 1] + 1,  # insertion
            d[i - 1][j - 1] + cost,  # substitution
        )

    return d[m][n]


def levenshtein_similarity(s1: str, s2: str) -> float:
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1 - (distance / max_len)
