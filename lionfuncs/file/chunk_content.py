from typing import Any, Callable, Literal

from .chunk_by_chars import chunk_by_chars
from .chunk_by_tokens import chunk_by_tokens


def chunk_content(
    content: str,
    chunk_by: Literal["chars", "tokens"] = "chars",
    tokenizer: Callable[[str], list[str]] = str.split,
    chunk_size: int = 1024,
    overlap: float = 0,
    threshold: int = 256,
    metadata: dict[str, Any] = {},
    return_tokens: bool = False,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """
    Split content into chunks and add metadata.

    This function takes a string content, splits it into chunks using the provided
    chunking function, and adds metadata to each chunk.

    Args:
        content (str): The content to be chunked.
        chunk_by(str): The method to use for chunking: "chars" or "tokens".
        tokenizer (Callable): The function to use for tokenization. defaults to str.split.
        chunk_size (int): The target size for each chunk.
        overlap (float): The fraction of overlap between chunks.
        threshold (int): The minimum size for the last chunk.
        metadata (Dict[str, Any]): Metadata to be included with each chunk.
        kwargs for tokenizer, if needed.


    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing a chunk with metadata.
    """

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
