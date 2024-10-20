def cosine_similarity(s1: str, s2: str) -> float:
    set1, set2 = set(s1), set(s2)
    intersection = set1.intersection(set2)
    return len(intersection) / ((len(set1) * len(set2)) ** 0.5)
