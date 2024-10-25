"""
Tests for string similarity functions.

This module provides comprehensive tests for all string similarity algorithms
including edge cases, special characters, and Unicode handling.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import pytest

from lionfuncs.algo.string_similarity import (
    SIMILARITY_ALGO_MAP,
    cosine_similarity,
    hamming_similarity,
    jaro_distance,
    jaro_winkler_similarity,
    levenshtein_distance,
    levenshtein_similarity,
    string_similarity,
)


# Cosine Similarity Tests
@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        ("hello", "hello", 1.0),
        ("", "", 0.0),
        ("hello", "", 0.0),
        ("abc", "def", 0.0),
        ("python", "pytohn", 1.0),  # Same characters, different order
        ("test", "tset", 1.0),  # Anagram
        ("aaa", "aaa", 1.0),  # Repeated characters
    ],
)
def test_cosine_similarity(s1: str, s2: str, expected: float) -> None:
    """Test cosine similarity function."""
    assert pytest.approx(cosine_similarity(s1, s2), abs=1e-3) == expected


# Hamming Similarity Tests
@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        ("hello", "hello", 1.0),
        ("hello", "hella", 0.8),
        ("", "", 0.0),
        ("hello", "world", 0.2),
        ("abc", "abd", 0.667),
        ("test", "pest", 0.75),
        ("11111", "11011", 0.8),
    ],
)
def test_hamming_similarity(s1: str, s2: str, expected: float) -> None:
    """Test Hamming similarity function."""
    assert pytest.approx(hamming_similarity(s1, s2), abs=1e-3) == expected


# Jaro Distance Tests
@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        ("string", "string", 1.0),
        ("abc", "xyz", 0.0),
        ("dwayne", "duane", 0.8222),
        ("", "", 1.0),
        ("abc", "", 0.0),
        ("", "xyz", 0.0),
        ("123456", "123", 0.8333),
        ("martha", "marhta", 0.9444),
        ("dixon", "dickson", 0.7905),
        ("jellyfish", "smellyfish", 0.8963),
    ],
)
def test_jaro_distance(s1: str, s2: str, expected: float) -> None:
    """Test Jaro distance function."""
    assert pytest.approx(jaro_distance(s1, s2), abs=1e-3) == expected


# Jaro-Winkler Similarity Tests
@pytest.mark.parametrize(
    "s1,s2,expected,scaling",
    [
        ("string", "string", 1.0, 0.1),
        ("abc", "xyz", 0.0, 0.1),
        ("dwayne", "duane", 0.8400, 0.1),
        ("", "", 1.0, 0.1),
        ("abc", "", 0.0, 0.1),
        ("", "xyz", 0.0, 0.1),
        ("123456", "123", 0.8833, 0.1),
        ("dwayne", "duane", 0.8578, 0.2),
        ("MARTHA", "MARHTA", 0.9611, 0.1),
        ("DIXON", "DICKSONX", 0.8133, 0.1),
    ],
)
def test_jaro_winkler_similarity_with_scaling(
    s1: str, s2: str, expected: float, scaling: float
) -> None:
    """Test Jaro-Winkler similarity function."""
    assert (
        pytest.approx(
            jaro_winkler_similarity(s1, s2, scaling=scaling), abs=1e-4
        )
        == expected
    )


def test_jaro_winkler_invalid_scaling() -> None:
    """Test invalid scaling factor."""
    with pytest.raises(ValueError):
        jaro_winkler_similarity("hello", "hello", scaling=0.5)


# Levenshtein Distance Tests
@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        ("string", "string", 0),
        ("abc", "xyz", 3),
        ("kitten", "sitting", 3),
        ("", "", 0),
        ("abc", "", 3),
        ("", "xyz", 3),
        ("123456", "123", 3),
        ("String", "string", 1),
        ("flaw", "lawn", 2),
        ("gumbo", "gambol", 2),
        ("saturday", "sunday", 3),
        ("pale", "bale", 1),
    ],
)
def test_levenshtein_distance(s1: str, s2: str, expected: int) -> None:
    """Test Levenshtein distance function."""
    assert levenshtein_distance(s1, s2) == expected


# Levenshtein Similarity Tests
@pytest.mark.parametrize(
    "s1,s2,expected",
    [
        ("hello", "hello", 1.0),
        ("hello", "helo", 0.8),
        ("", "", 1.0),
        ("", "hello", 0.0),
        ("hello", "", 0.0),
        ("sitting", "kitten", 0.571),
        ("sunday", "saturday", 0.625),
        ("pale", "bale", 0.75),
        ("pale", "bake", 0.5),
    ],
)
def test_levenshtein_similarity(s1: str, s2: str, expected: float) -> None:
    """Test Levenshtein similarity function."""
    assert pytest.approx(levenshtein_similarity(s1, s2), abs=1e-3) == expected


def test_similarity_algorithms_bounds() -> None:
    """Test algorithm bounds (0-1)."""
    test_cases = [
        ("hello", "hello"),
        ("hello", "world"),
        ("", ""),
        ("a", ""),
        ("", "a"),
        ("a", "a"),
        ("ab", "ba"),
        ("aaa", "aaa"),
    ]

    for algo_name, func in SIMILARITY_ALGO_MAP.items():
        for s1, s2 in test_cases:
            score = func(s1, s2)
            assert (
                0 <= score <= 1
            ), "Algorithm {} returned {} for {}, {}".format(
                algo_name, score, s1, s2
            )


def test_all_algorithms_handle_special_characters() -> None:
    """Test special character handling."""
    special_chars = "!@#$%^&*()"
    normal_text = "hello"

    for algo_name, func in SIMILARITY_ALGO_MAP.items():
        score1 = func(special_chars, special_chars)
        assert score1 == 1.0

        score2 = func(normal_text + special_chars, normal_text)
        assert 0 <= score2 <= 1


def test_all_algorithms_handle_unicode() -> None:
    """Test Unicode character handling."""
    unicode_text1 = "hello世界"
    unicode_text2 = "hello世界"

    for algo_name, func in SIMILARITY_ALGO_MAP.items():
        if algo_name == "hamming":
            continue
        score = func(unicode_text1, unicode_text2)
        assert score == 1.0


def test_all_algorithms_handle_long_strings() -> None:
    """Test long string handling."""
    long_text1 = "a" * 1000
    long_text2 = "a" * 999 + "b"

    for algo_name, func in SIMILARITY_ALGO_MAP.items():
        if algo_name == "hamming":
            continue
        score = func(long_text1, long_text2)
        assert 0 <= score <= 1


def custom_similarity(s1: str, s2: str) -> float:
    """Custom similarity function."""
    return 1.0 if s1 == s2 else 0.0


# Basic functionality tests
@pytest.mark.parametrize(
    "word,words,algorithm,expected",
    [
        ("hello", ["hello", "world"], "levenshtein", "hello"),
        ("hellp", ["help", "hello"], "levenshtein", "help"),
        ("martha", ["marhta", "market"], "jaro_winkler", "marhta"),
        ("python", ["pytohn", "perl"], "cosine", "pytohn"),
        ("hello", ["hellp", "help"], "hamming", "hellp"),
        ("hello", ["helo", "hell"], "sequence_matcher", "helo"),
    ],
)
def test_string_similarity_basic(
    word: str, words: List[str], algorithm: str, expected: str
) -> None:
    """Test basic functionality."""
    result = string_similarity(
        word, words, algorithm=algorithm, return_most_similar=True
    )
    assert result == expected


@pytest.mark.parametrize(
    "word,words,threshold,expected",
    [
        ("hello", ["hello", "help", "world"], 0.8, ["hello", "help"]),
        ("hello", ["hello", "help", "world"], 0.9, ["hello"]),
        ("hello", ["world", "bye"], 0.8, None),
    ],
)
def test_string_similarity_threshold(
    word: str,
    words: List[str],
    threshold: float,
    expected: Optional[List[str]],
) -> None:
    """Test threshold filtering."""
    result = string_similarity(word, words, threshold=threshold)
    assert result == expected


@pytest.mark.parametrize(
    "word,words,case_sensitive,expected",
    [
        ("HELLO", ["hello", "HELLO"], False, ["hello", "HELLO"]),
        ("HELLO", ["hello", "HELLO"], True, ["HELLO"]),
        ("Python", ["python", "PYTHON"], False, ["python", "PYTHON"]),
    ],
)
def test_string_similarity_case_sensitivity(
    word: str, words: List[str], case_sensitive: bool, expected: List[str]
) -> None:
    """Test case sensitivity."""
    result = string_similarity(word, words, case_sensitive=case_sensitive)
    assert result == expected


@pytest.mark.parametrize(
    "word,words,expected",
    [
        ("hello", ["hello", "help", "world"], "hello"),
        ("hellp", ["help", "hello", "world"], "help"),
    ],
)
def test_string_similarity_most_similar(
    word: str, words: List[str], expected: str
) -> None:
    """Test most similar result."""
    result = string_similarity(word, words, return_most_similar=True)
    assert result == expected


def test_string_similarity_custom_function() -> None:
    """Test custom similarity function."""
    result = string_similarity(
        "hello",
        ["world", "hello"],
        algorithm=custom_similarity,
    )
    assert result == ["hello", "world"]


def test_string_similarity_errors() -> None:
    """Test error handling."""
    with pytest.raises(ValueError):
        string_similarity("hello", [])

    with pytest.raises(ValueError):
        string_similarity("hello", ["world"], threshold=2.0)

    with pytest.raises(ValueError):
        string_similarity("hello", ["world"], algorithm="invalid")

    with pytest.raises(ValueError):
        string_similarity("hello", ["world"], algorithm=123)  # type: ignore


def test_string_similarity_edge_cases() -> None:
    """Test edge cases."""
    assert string_similarity("", ["", "a"], return_most_similar=True) == ""
    assert string_similarity("a", ["a", "b"], return_most_similar=True) == "a"
    assert (
        string_similarity(
            "hello世界", ["hello世界", "hello"], return_most_similar=True
        )
        == "hello世界"
    )
    assert (
        string_similarity("123", ["123", "456"], return_most_similar=True)
        == "123"
    )
    assert (
        string_similarity("!@#", ["!@#", "abc"], return_most_similar=True)
        == "!@#"
    )


def test_string_similarity_with_threshold() -> None:
    """Test threshold behavior."""
    for algo in ["levenshtein", "jaro_winkler", "cosine"]:
        result = string_similarity(
            "hello", ["hello", "help"], algorithm=algo, threshold=0.5
        )
        assert result and "hello" in result

        result = string_similarity(
            "hello", ["help", "world"], algorithm=algo, threshold=0.9
        )
        assert result is None


def test_all_algorithms_handle_nonstring() -> None:
    """Test non-string input."""
    for algo in ["levenshtein", "jaro_winkler", "cosine"]:
        result = string_similarity(123, [123, 456], algorithm=algo)
        assert isinstance(result[0], str)


__all__ = ["test_jaro_winkler_similarity_with_scaling"]
