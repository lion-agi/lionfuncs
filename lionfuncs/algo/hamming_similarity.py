def hamming_similarity(s1: str, s2: str) -> float:
    if len(s1) != len(s2):
        return 0.0
    return sum(c1 == c2 for c1, c2 in zip(s1, s2)) / len(s1)
