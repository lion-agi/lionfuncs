from collections.abc import Callable, Sequence
from difflib import SequenceMatcher
from typing import Literal, TypeVar, overload

from lionfuncs.algo.cosine_similarity import cosine_similarity
from lionfuncs.algo.hamming_similarity import hamming_similarity
from lionfuncs.algo.jaro_distance import jaro_winkler_similarity
from lionfuncs.algo.levenshtein_distance import levenshtein_similarity

T = TypeVar("T")

AlgorithmType = Literal[
    "jaro_winkler", "levenshtein", "sequence_matcher", "hamming", "cosine"
]


class MatchResult:
    def __init__(self, word: str, score: float, index: int):
        self.word = word
        self.score = score
        self.index = index


@overload
def choose_most_similar(
    word: str,
    correct_words: Sequence[T],
    *,
    algorithm: (
        Literal[
            "jaro_winkler",
            "levenshtein",
            "sequence_matcher",
            "hamming",
            "cosine",
        ]
        | Callable[[str, str], float]
    ) = "jaro_winkler",
    threshold: float = 0.0,
    case_sensitive: bool = False,
    return_all: Literal[False] = False,
    sort_results: bool = True,
    limit: int | None = None,
) -> T | None: ...


@overload
def choose_most_similar(
    word: str,
    correct_words: Sequence[T],
    *,
    algorithm: (
        Literal[
            "jaro_winkler",
            "levenshtein",
            "sequence_matcher",
            "hamming",
            "cosine",
        ]
        | Callable[[str, str], float]
    ) = "jaro_winkler",
    threshold: float = 0.0,
    case_sensitive: bool = False,
    return_all: Literal[True],
    sort_results: bool = True,
    limit: int | None = None,
) -> list[MatchResult]: ...


def choose_most_similar(
    word: str,
    correct_words: Sequence[T],
    *,
    algorithm: (
        Literal[
            "jaro_winkler",
            "levenshtein",
            "sequence_matcher",
            "hamming",
            "cosine",
        ]
        | Callable[[str, str], float]
    ) = "jaro_winkler",
    threshold: float = 0.0,
    case_sensitive: bool = False,
    return_all: bool = False,
    sort_results: bool = True,
    limit: int | None = None,
) -> T | list[MatchResult] | None:
    """
    Choose the most similar word(s) from a list of correct words.

    This function compares the input word against a list of correct words
    using a specified similarity algorithm, and returns the most similar word(s).

    Args:
        word: The word to compare.
        correct_words: The sequence of correct words to compare against.
        algorithm: The similarity algorithm to use. Can be a string specifying
            a built-in algorithm or a custom function.
        threshold: The minimum similarity score to consider a match.
        case_sensitive: Whether the comparison should be case-sensitive.
        return_all: If True, returns all matches above the threshold.
        sort_results: If True and return_all is True, sorts results by score.
        limit: Maximum number of results to return when return_all is True.

    Returns:
        If return_all is False, returns the most similar word or None if no
        matches are found. If return_all is True, returns a list of MatchResult
        objects for all matches above the threshold.

    Raises:
        ValueError: If correct_words is empty or algorithm is invalid.

    Examples:
        >>> words = ['apple', 'banana', 'cherry']
        >>> choose_most_similar('aple', words)
        'apple'

        >>> choose_most_similar('banan', words, return_all=True, threshold=0.5)
        [MatchResult(word='banana', score=0.9166666666666666, index=1),
         MatchResult(word='apple', score=0.6666666666666666, index=0)]

        >>> choose_most_similar('grape', words, algorithm="levenshtein", threshold=0.5)
        None

    Notes:
        Available built-in algorithms:
        - "jaro_winkler": Good for short strings like names.
        - "levenshtein": Measures the minimum number of single-character edits.
        - "sequence_matcher": Uses Python's difflib, good for longer texts.
        - "hamming": Compares strings of equal length, counts positions with different characters.
        - "cosine": Measures similarity between two strings irrespective of word order.
    """
    if not correct_words:
        raise ValueError("correct_words must not be empty")

    algorithm_map: dict[str, Callable[[str, str], float]] = {
        "jaro_winkler": jaro_winkler_similarity,
        "levenshtein": levenshtein_similarity,
        "sequence_matcher": lambda s1, s2: SequenceMatcher(
            None, s1, s2
        ).ratio(),
        "hamming": hamming_similarity,
        "cosine": cosine_similarity,
    }

    if isinstance(algorithm, str):
        score_func = algorithm_map.get(algorithm)
        if score_func is None:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    elif callable(algorithm):
        score_func = algorithm
    else:
        raise ValueError(
            "algorithm must be a string specifying a built-in algorithm or a callable"
        )

    if not case_sensitive:
        word = word.lower()
        correct_words = [str(w).lower() for w in correct_words]

    results = []
    for idx, correct_word in enumerate(correct_words):
        score = score_func(word, str(correct_word))
        if score >= threshold:
            results.append(MatchResult(str(correct_word), score, idx))

    if not results:
        return [] if return_all else None

    if sort_results:
        results.sort(key=lambda x: x.score, reverse=True)

    if limit is not None:
        results = results[:limit]

    if return_all:
        return results
    else:
        return correct_words[results[0].index]
