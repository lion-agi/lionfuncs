import math


def chunk_by_chars(
    text: str, chunk_size: int = 2048, overlap: float = 0, threshold: int = 256
) -> list[str]:
    """
    Split a text into chunks of approximately equal size, with optional overlap.

    This function divides the input text into chunks based on the specified
    chunk size. It handles different scenarios based on the number of chunks
    required and provides options for overlap between chunks.

    Args:
        text (str): The input text to be chunked.
        chunk_size (int, optional): The target size for each chunk. Defaults to 2048.
        overlap (float, optional): The fraction of overlap between chunks. Defaults to 0.
        threshold (int, optional): The minimum size for the last chunk. Defaults to 256.

    Returns:
        List[str]: A list of text chunks.

    Raises:
        ValueError: If an error occurs during the chunking process.

    Examples:
        >>> text = "This is a sample text for chunking."
        >>> chunks = chunk_by_chars(text, chunk_size=10, overlap=0.2)
        >>> print(chunks)
        ['This is a ', 'a sample ', 'le text fo', 'for chunki', 'king.']
    """
    try:
        n_chunks = math.ceil(len(text) / chunk_size)
        overlap_size = int(chunk_size * overlap / 2)

        if n_chunks == 1:
            return [text]
        elif n_chunks == 2:
            return _chunk_two_parts(text, chunk_size, overlap_size, threshold)
        else:
            return _chunk_multiple_parts(
                text, chunk_size, overlap_size, n_chunks, threshold
            )
    except Exception as e:
        raise ValueError(f"An error occurred while chunking the text: {e}")


def _chunk_two_parts(
    text: str, chunk_size: int, overlap_size: int, threshold: int
) -> list[str]:
    """Handle chunking for two parts."""
    first_chunk = text[: chunk_size + overlap_size]
    if len(text) - chunk_size > threshold:
        return [first_chunk, text[chunk_size - overlap_size :]]
    return [text]


def _chunk_multiple_parts(
    text: str,
    chunk_size: int,
    overlap_size: int,
    n_chunks: int,
    threshold: int,
) -> list[str]:
    """Handle chunking for more than two parts."""
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
