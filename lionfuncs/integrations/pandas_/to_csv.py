from pathlib import Path
from typing import Any

from lionfuncs.file_handlers.create_path import create_path

from .to_df import to_df


def to_csv(
    input_: Any,
    /,
    *,
    directory: str | Path,
    filename: str,
    timestamp: bool = False,
    random_hash_digits: int = 0,
    drop_how: str = "all",
    drop_kwargs: dict | None = None,
    reset_index: bool = True,
    concat_kwargs: dict | None = None,
    df_kwargs: dict = None,
    path_kwargs: dict = None,
    verbose: bool = False,
) -> None:
    df = to_df(
        input_,
        drop_how=drop_how,
        drop_kwargs=drop_kwargs,
        reset_index=reset_index,
        concat_kwargs=concat_kwargs,
        **(df_kwargs or {}),
    )
    fp = create_path(
        directory=directory,
        filename=filename,
        timestamp=timestamp,
        random_hash_digits=random_hash_digits,
        extension="csv",
        **(path_kwargs or {}),
    )
    df.to_csv(fp, index=False)
    if verbose:
        print(f"Data saved to {fp}")


def to_excel(
    input_: Any,
    /,
    *,
    directory: str | Path,
    filename: str,
    timestamp: bool = False,
    random_hash_digits: int = 0,
    drop_how: str = "all",
    drop_kwargs: dict | None = None,
    reset_index: bool = True,
    concat_kwargs: dict | None = None,
    df_kwargs: dict = None,
    path_kwargs: dict = None,
    verbose: bool = False,
) -> None:
    df = to_df(
        input_,
        drop_how=drop_how,
        drop_kwargs=drop_kwargs,
        reset_index=reset_index,
        concat_kwargs=concat_kwargs,
        **(df_kwargs or {}),
    )
    fp = create_path(
        directory=directory,
        filename=filename,
        timestamp=timestamp,
        random_hash_digits=random_hash_digits,
        extension="xlsx",
        **(path_kwargs or {}),
    )
    df.to_excel(fp, index=False)
    if verbose:
        print(f"Data saved to {fp}")


__all__ = ["to_csv", "to_excel"]
