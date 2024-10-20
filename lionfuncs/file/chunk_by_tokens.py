import math


def chunk_by_tokens(
    tokens: list[str],
    chunk_size: int = 1024,
    overlap: float = 0,
    threshold: int = 128,
    return_tokens: bool = False,
) -> list[str | list[str]]:
    """
    Split a list of tokens into chunks of approximately equal size, with optional overlap.

    This function divides the input tokens into chunks based on the specified
    chunk size. It handles different scenarios based on the number of chunks
    required and provides options for overlap between chunks.

    Args:
        tokens (list[str]): The input list of tokens to be chunked.
        chunk_size (int, optional): The target size for each chunk. Defaults to 1024.
        overlap (float, optional): The fraction of overlap between chunks. Defaults to 0.
        threshold (int, optional): The minimum size for the last chunk. Defaults to 128.
        return_tokens (bool, optional): If True, return chunks as lists of tokens;
                                        if False, return as joined strings. Defaults to False.

    Returns:
        list[Union[str, list[str]]]: A list of chunked tokens, either as strings or token lists.

    Raises:
        ValueError: If an error occurs during the chunking process.

    Examples:
        >>> tokens = ["This", "is", "a", "sample", "text", "for", "chunking."]
        >>> chunks = chunk_by_tokens(tokens, chunk_size=3, overlap=0.2)
        >>> print(chunks)
        ['This is a', 'a sample text', 'text for chunking.']
    """
    try:
        n_chunks = math.ceil(len(tokens) / chunk_size)
        overlap_size = int(overlap * chunk_size / 2)
        residue = len(tokens) % chunk_size

        if n_chunks == 1:
            return _process_single_chunk(tokens, return_tokens)
        elif n_chunks == 2:
            return _chunk_two_parts(
                tokens,
                chunk_size,
                overlap_size,
                threshold,
                residue,
                return_tokens,
            )
        else:
            return _chunk_multiple_parts(
                tokens,
                chunk_size,
                overlap_size,
                n_chunks,
                threshold,
                residue,
                return_tokens,
            )
    except Exception as e:
        raise ValueError(f"An error occurred while chunking the tokens: {e}")


def _process_single_chunk(
    tokens: list[str], return_tokens: bool
) -> list[str | list[str]]:
    """Handle processing for a single chunk."""
    return [tokens] if return_tokens else [" ".join(tokens).strip()]


def _chunk_two_parts(
    tokens: list[str],
    chunk_size: int,
    overlap_size: int,
    threshold: int,
    residue: int,
    return_tokens: bool,
) -> list[str | list[str]]:
    """Handle chunking for two parts."""
    chunks = [tokens[: chunk_size + overlap_size]]
    if residue > threshold:
        chunks.append(tokens[chunk_size - overlap_size :])
    else:
        return _process_single_chunk(tokens, return_tokens)
    return _format_chunks(chunks, return_tokens)


def _chunk_multiple_parts(
    tokens: list[str],
    chunk_size: int,
    overlap_size: int,
    n_chunks: int,
    threshold: int,
    residue: int,
    return_tokens: bool,
) -> list[str | list[str]]:
    """Handle chunking for more than two parts."""
    chunks = [tokens[: chunk_size + overlap_size]]
    for i in range(1, n_chunks - 1):
        start_idx = chunk_size * i - overlap_size
        end_idx = chunk_size * (i + 1) + overlap_size
        chunks.append(tokens[start_idx:end_idx])

    last_chunk_start = chunk_size * (n_chunks - 1) - overlap_size
    if len(tokens) - last_chunk_start > threshold:
        chunks.append(tokens[last_chunk_start:])
    else:
        chunks[-1] += tokens[-residue:]

    return _format_chunks(chunks, return_tokens)


def _format_chunks(
    chunks: list[list[str]], return_tokens: bool
) -> list[str | list[str]]:
    """Format chunks based on the return_tokens flag."""
    return (
        chunks
        if return_tokens
        else [" ".join(chunk).strip() for chunk in chunks]
    )
