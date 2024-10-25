"""Content chunking utilities.

This module provides utilities for splitting content into chunks, supporting
both character-based and token-based chunking with configurable overlap
and size options.
"""

from __future__ import annotations

import math
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Union,
    overload,
)


def chunk_by_chars(
    text: str, chunk_size: int = 2048, overlap: float = 0, threshold: int = 256
) -> List[str]:
    """Split text into chunks with optional overlap.

    Args:
        text: Input text to chunk.
        chunk_size: Target size for each chunk.
        overlap: Fraction of overlap between chunks (0-1).
        threshold: Minimum size for last chunk.

    Returns:
        List of text chunks.

    Raises:
        ValueError: Invalid parameters or chunking error.

    Examples:
        >>> text = "This is some text to chunk."
        >>> chunks = chunk_by_chars(text, chunk_size=10, overlap=0.2)
        >>> print(chunks)
        ['This is so', 'some text ', 'text to ch', 'to chunk.']
    """
    if not text:
        return []

    if not 0 <= overlap < 1:
        raise ValueError("Overlap must be between 0 and 1")

    if chunk_size < 1:
        raise ValueError("Chunk size must be positive")

    if threshold < 0:
        raise ValueError("Threshold must be non-negative")

    try:
        n_chunks = math.ceil(len(text) / chunk_size)
        overlap_size = int(chunk_size * overlap / 2)

        if n_chunks == 1:
            return [text]
        elif n_chunks == 2:
            return _chunk_two_parts_chars(
                text, chunk_size, overlap_size, threshold
            )
        else:
            return _chunk_multiple_parts_chars(
                text, chunk_size, overlap_size, n_chunks, threshold
            )
    except Exception as e:
        raise ValueError(f"Error chunking text: {e}")


def chunk_by_tokens(
    tokens: List[str],
    chunk_size: int = 1024,
    overlap: float = 0,
    threshold: int = 128,
    return_tokens: bool = False,
) -> List[Union[str, List[str]]]:
    """Split tokens into chunks with optional overlap.

    Args:
        tokens: Input tokens to chunk.
        chunk_size: Target number of tokens per chunk.
        overlap: Fraction of overlap between chunks (0-1).
        threshold: Minimum tokens for last chunk.
        return_tokens: If True, return token lists instead of strings.

    Returns:
        List of chunks (either strings or token lists).

    Raises:
        ValueError: Invalid parameters or chunking error.

    Examples:
        >>> tokens = ["This", "is", "a", "test"]
        >>> chunks = chunk_by_tokens(tokens, chunk_size=2, overlap=0.5)
        >>> print(chunks)
        ['This is', 'is a', 'a test']
    """
    if not tokens:
        return []

    if not 0 <= overlap < 1:
        raise ValueError("Overlap must be between 0 and 1")

    if chunk_size < 1:
        raise ValueError("Chunk size must be positive")

    if threshold < 0:
        raise ValueError("Threshold must be non-negative")

    try:
        n_chunks = math.ceil(len(tokens) / chunk_size)
        overlap_size = int(overlap * chunk_size / 2)
        residue = len(tokens) % chunk_size

        if n_chunks == 1:
            return _process_single_chunk(tokens, return_tokens)
        elif n_chunks == 2:
            return _chunk_two_parts_tokens(
                tokens,
                chunk_size,
                overlap_size,
                threshold,
                residue,
                return_tokens,
            )
        else:
            return _chunk_multiple_parts_tokens(
                tokens,
                chunk_size,
                overlap_size,
                n_chunks,
                threshold,
                residue,
                return_tokens,
            )
    except Exception as e:
        raise ValueError(f"Error chunking tokens: {e}")


@overload
def chunk_content(
    content: str,
    chunk_by: Literal["chars"] = "chars",
    chunk_size: int = 2048,
    overlap: float = 0,
    threshold: int = 256,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]: ...


@overload
def chunk_content(
    content: str,
    chunk_by: Literal["tokens"],
    tokenizer: Callable = str.split,
    chunk_size: int = 1024,
    overlap: float = 0,
    threshold: int = 128,
    metadata: Optional[Dict[str, Any]] = None,
    return_tokens: bool = False,
    **kwargs: Any,
) -> List[Dict[str, Any]]: ...


def chunk_content(
    content: str,
    chunk_by: Literal["chars", "tokens"] = "chars",
    tokenizer: Callable = str.split,
    chunk_size: int = 2048,
    overlap: float = 0,
    threshold: int = 256,
    metadata: Optional[Dict[str, Any]] = None,
    return_tokens: bool = False,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """Split content into chunks with metadata.

    Args:
        content: Content to chunk.
        chunk_by: Chunking method ("chars" or "tokens").
        tokenizer: Function to tokenize content.
        chunk_size: Target chunk size.
        overlap: Overlap fraction (0-1).
        threshold: Minimum chunk size.
        metadata: Additional metadata for chunks.
        return_tokens: Return token lists for token mode.
        **kwargs: Additional tokenizer arguments.

    Returns:
        List of chunk dictionaries with metadata.

    Examples:
        >>> content = "This is some text to chunk."
        >>> chunks = chunk_content(content, chunk_size=10)
        >>> print(chunks)
        [{'chunk_content': 'This is so',
          'chunk_id': 1, 'total_chunks': 3, ...}]
    """
    if not content:
        return []

    metadata = metadata or {}

    if chunk_by == "tokens":
        chunks = chunk_by_tokens(
            tokens=tokenizer(content, **kwargs),
            chunk_size=chunk_size,
            overlap=overlap,
            threshold=threshold,
            return_tokens=return_tokens,
        )
    else:
        chunks = chunk_by_chars(
            text=content,
            chunk_size=chunk_size,
            overlap=overlap,
            threshold=threshold,
        )

    return [
        {
            "chunk_content": chunk,
            "chunk_id": i + 1,
            "total_chunks": len(chunks),
            "chunk_size": len(chunk),
            **metadata,
        }
        for i, chunk in enumerate(chunks)
    ]


def _chunk_two_parts_chars(
    text: str,
    chunk_size: int,
    overlap_size: int,
    threshold: int,
) -> List[str]:
    """Handle two-part character chunking."""
    first_chunk = text[: chunk_size + overlap_size]
    if len(text) - chunk_size > threshold:
        return [first_chunk, text[chunk_size - overlap_size :]]
    return [text]


def _chunk_multiple_parts_chars(
    text: str,
    chunk_size: int,
    overlap_size: int,
    n_chunks: int,
    threshold: int,
) -> List[str]:
    """Handle multi-part character chunking."""
    chunks = [text[: chunk_size + overlap_size]]

    for i in range(1, n_chunks - 1):
        start_idx = chunk_size * i - overlap_size
        end_idx = chunk_size * (i + 1) + overlap_size
        chunks.append(text[start_idx:end_idx])

    last_chunk_start = chunk_size * (n_chunks - 1) - overlap_size
    if len(text) - last_chunk_start > threshold:
        chunks.append(text[last_chunk_start:])
    else:
        chunks[-1] += text[chunk_size * (n_chunks - 1) + overlap_size :]

    return chunks


def _process_single_chunk(
    tokens: List[str],
    return_tokens: bool,
) -> List[Union[str, List[str]]]:
    """Handle single chunk processing for tokens."""
    return [tokens] if return_tokens else [" ".join(tokens)]


def _chunk_two_parts_tokens(
    tokens: List[str],
    chunk_size: int,
    overlap_size: int,
    threshold: int,
    residue: int,
    return_tokens: bool,
) -> List[Union[str, List[str]]]:
    """Handle two-part token chunking."""
    chunks = [tokens[: chunk_size + overlap_size]]
    if residue > threshold:
        chunks.append(tokens[chunk_size - overlap_size :])
    else:
        return _process_single_chunk(tokens, return_tokens)
    return _format_chunks(chunks, return_tokens)


def _chunk_multiple_parts_tokens(
    tokens: List[str],
    chunk_size: int,
    overlap_size: int,
    n_chunks: int,
    threshold: int,
    residue: int,
    return_tokens: bool,
) -> List[Union[str, List[str]]]:
    """Handle multi-part token chunking."""
    chunks = [tokens[: chunk_size + overlap_size]]

    for i in range(1, n_chunks - 1):
        start_idx = chunk_size * i - overlap_size
        end_idx = chunk_size * (i + 1) + overlap_size
        chunks.append(tokens[start_idx:end_idx])

    last_chunk_start = chunk_size * (n_chunks - 1) - overlap_size
    if len(tokens) - last_chunk_start > threshold:
        chunks.append(tokens[last_chunk_start:])
    else:
        chunks[-1].extend(tokens[-residue:])

    return _format_chunks(chunks, return_tokens)


def _format_chunks(
    chunks: List[List[str]],
    return_tokens: bool,
) -> List[Union[str, List[str]]]:
    """Format token chunks based on return type."""
    return chunks if return_tokens else [" ".join(chunk) for chunk in chunks]


__all__ = [
    "chunk_by_chars",
    "chunk_by_tokens",
    "chunk_content",
]
