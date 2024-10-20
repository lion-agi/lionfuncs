import json
from pathlib import Path
from typing import Any, Callable

from lionfuncs.file.chunk_content import chunk_content
from lionfuncs.file.create_path import create_path
from lionfuncs.file.save_to_file import save_to_file


def file_to_chunks(
    file_path: str | Path,
    chunk_func: Callable[[str, int, float, int], list[str]],
    chunk_size: int = 1500,
    overlap: float = 0.1,
    threshold: int = 200,
    encoding: str = "utf-8",
    custom_metadata: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    verbose: bool = False,
    timestamp: bool = True,
    random_hash_digits: int = 4,
) -> list[dict[str, Any]]:
    """
    Process a file and split its content into chunks.

    This function reads a file, splits its content into chunks using the provided
    chunking function, and optionally saves the chunks to separate files.

    Args:
        file_path (Union[str, Path]): Path to the file to be processed.
        chunk_func (Callable): Function to use for chunking the content.
        chunk_size (int): The target size for each chunk.
        overlap (float): The fraction of overlap between chunks.
        threshold (int): The minimum size for the last chunk.
        encoding (str): File encoding to use when reading the file.
        custom_metadata (Optional[Dict[str, Any]]): Additional metadata to include with each chunk.
        output_dir (Optional[Union[str, Path]]): Directory to save output chunks (if provided).
        verbose (bool): If True, print verbose output.
        timestamp (bool): If True, include timestamp in output filenames.
        random_hash_digits (int): Number of random hash digits to include in output filenames.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing a chunk with metadata.

    Raises:
        ValueError: If there's an error processing the file.
    """
    try:
        file_path = Path(file_path)
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()

        metadata = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            **(custom_metadata or {}),
        }

        chunks = chunk_content(
            content, chunk_func, chunk_size, overlap, threshold, metadata
        )

        if output_dir:
            save_chunks(
                chunks, output_dir, verbose, timestamp, random_hash_digits
            )

        return chunks
    except Exception as e:
        raise ValueError(f"Error processing file {file_path}: {e}") from e


def save_chunks(
    chunks: list[dict[str, Any]],
    output_dir: str | Path,
    verbose: bool,
    timestamp: bool,
    random_hash_digits: int,
) -> None:
    """Helper function to save chunks to files."""
    output_path = Path(output_dir)
    for i, chunk in enumerate(chunks):
        file_path = create_path(
            directory=output_path,
            filename=f"chunk_{i+1}",
            extension="json",
            timestamp=timestamp,
            random_hash_digits=random_hash_digits,
        )
        save_to_file(
            json.dumps(chunk, ensure_ascii=False, indent=2),
            directory=file_path.parent,
            filename=file_path.name,
            verbose=verbose,
        )
