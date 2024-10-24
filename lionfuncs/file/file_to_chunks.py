import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


def file_to_chunks(
    file_path: Union[str, Path],
    *,
    chunk_size: int = 1500,
    overlap: float = 0.1,
    threshold: int = 200,
    encoding: str = "utf-8",
    chunk_by: str = "chars",
    tokenizer: Optional[Callable[[str], List[str]]] = None,
    custom_metadata: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    verbose: bool = False,
    timestamp: bool = True,
    random_hash_digits: int = 4,
) -> List[Dict[str, Any]]:
    """Process file content into chunks with metadata.

    Reads a file, splits its content into chunks, and optionally saves
    chunks to separate files with metadata.

    Args:
        file_path: Path to input file.
        chunk_size: Target chunk size.
        overlap: Overlap fraction between chunks.
        threshold: Minimum chunk size.
        encoding: File encoding.
        chunk_by: Chunking method ("chars" or "tokens").
        tokenizer: Custom tokenizer function.
        custom_metadata: Additional metadata for chunks.
        output_dir: Directory to save chunk files.
        verbose: Enable detailed logging.
        timestamp: Add timestamps to output files.
        random_hash_digits: Add random hash to output files.

    Returns:
        List of chunk dictionaries with metadata.

    Raises:
        ValueError: Invalid file or processing error.
        FileNotFoundError: Input file not found.
        UnicodeError: Encoding error.

    Examples:
        >>> chunks = file_to_chunks('doc.txt', chunk_size=1000)
        >>> print(f"Split into {len(chunks)} chunks")
    """
    try:
        file_path = Path(file_path)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        if verbose:
            logging.info(f"Processing file: {file_path}")

        # Read file content
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
        except UnicodeError as e:
            raise UnicodeError(f"Error reading {file_path}: {e}")

        # Prepare metadata
        metadata = {
            "source_file": str(file_path),
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            **(custom_metadata or {}),
        }

        # Create chunks
        chunks = chunk_content(
            content=content,
            chunk_by=chunk_by,
            tokenizer=tokenizer or str.split,
            chunk_size=chunk_size,
            overlap=overlap,
            threshold=threshold,
            metadata=metadata,
        )

        if verbose:
            logging.info(f"Created {len(chunks)} chunks from {file_path}")

        # Save chunks if output directory specified
        if output_dir:
            save_chunks(
                chunks=chunks,
                output_dir=output_dir,
                verbose=verbose,
                timestamp=timestamp,
                random_hash_digits=random_hash_digits,
            )

        return chunks

    except Exception as e:
        raise ValueError(f"Error processing {file_path}: {e}")


def save_chunks(
    chunks: List[Dict[str, Any]],
    output_dir: Union[str, Path],
    verbose: bool = False,
    timestamp: bool = True,
    random_hash_digits: int = 4,
) -> None:
    """Save chunks to individual files.

    Helper function to save chunk dictionaries as JSON files.

    Args:
        chunks: List of chunk dictionaries.
        output_dir: Output directory.
        verbose: Enable detailed logging.
        timestamp: Add timestamps to filenames.
        random_hash_digits: Add random hash to filenames.

    Raises:
        ValueError: Error saving chunks.
    """
    from .path_ import create_path

    output_dir = Path(output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, chunk in enumerate(chunks, 1):
            try:
                file_path = create_path(
                    directory=output_dir,
                    filename=f"chunk_{i}",
                    extension="json",
                    timestamp=timestamp,
                    random_hash_digits=random_hash_digits,
                )

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=2)

                if verbose:
                    logging.info(f"Saved chunk {i} to {file_path}")

            except Exception as e:
                raise ValueError(f"Error saving chunk {i}: {e}")

    except Exception as e:
        raise ValueError(f"Error saving chunks to {output_dir}: {e}")
