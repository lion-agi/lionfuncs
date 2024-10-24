"""
Pandas utilities for data manipulation, file I/O, and DataFrame operations.

Features:
- DataFrame conversion and manipulation
- CSV/JSON/Excel file handling
- Search and replace operations
- Flexible data format handling
- Robust error handling
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import pandas as pd
from pandas import DataFrame, Series, concat
from pandas.core.generic import NDFrame

from lionfuncs.file.path_ import create_path
from lionfuncs.parse.to_dict import to_dict
from lionfuncs.parse.to_list import to_list


def to_df(
    input_: Any,
    /,
    *,
    drop_how: str = "all",
    drop_kwargs: Optional[Dict[str, Any]] = None,
    reset_index: bool = True,
    concat_kwargs: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> DataFrame:
    """
    Convert various input types to a pandas DataFrame.

    Args:
        input_: The input data to convert.
        drop_how: How to drop NA values ("any" or "all").
        drop_kwargs: Additional arguments for dropna().
        reset_index: Whether to reset index.
        concat_kwargs: Arguments for pandas.concat().
        **kwargs: Additional DataFrame constructor arguments.

    Returns:
        DataFrame: Converted DataFrame.

    Example:
        >>> data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        >>> df = to_df(data)
    """
    if not isinstance(input_, list):
        try:
            return general_to_df(
                input_,
                drop_how=drop_how,
                drop_kwargs=drop_kwargs,
                reset_index=reset_index,
                **kwargs,
            )
        except ValueError:
            input_ = [input_]

    if isinstance(input_, list):
        try:
            return _list_to_df(
                input_,
                drop_how=drop_how,
                drop_kwargs=drop_kwargs,
                reset_index=reset_index,
                concat_kwargs=concat_kwargs or {},
                **kwargs,
            )
        except ValueError:
            try:
                _d = [to_dict(i) for i in input_]
                return _list_to_df(
                    _d,
                    drop_how=drop_how,
                    drop_kwargs=drop_kwargs,
                    reset_index=reset_index,
                    concat_kwargs=concat_kwargs or {},
                    **kwargs,
                )
            except ValueError:
                raise ValueError(
                    "Error converting input_ to DataFrame"
                ) from None


def read_csv(
    filepath: str,
    chunk_size: Optional[int] = None,
    low_memory: bool = False,
    return_as: str = "dataframe",
    **kwargs: Any,
) -> Union[DataFrame, str, List, Dict]:
    """
    Read CSV file into DataFrame with optional chunking.

    Args:
        filepath: Path to CSV file.
        chunk_size: Number of rows per chunk.
        low_memory: Process in chunks to save memory.
        return_as: Format to return ('dataframe', 'json', 'jsonl', 'dict').
        **kwargs: Additional pandas.read_csv arguments.

    Returns:
        Data in specified format.

    Example:
        >>> df = read_csv('data.csv', return_as='dataframe')
    """
    try:
        if chunk_size:
            return pd.read_csv(
                filepath, chunksize=chunk_size, low_memory=low_memory, **kwargs
            )
        df = pd.read_csv(filepath, low_memory=low_memory, **kwargs)
        df = to_df(df)

        if return_as == "dataframe":
            return df
        elif return_as == "json":
            return df.to_json(orient="records")
        elif return_as == "jsonl":
            return df.to_json(orient="records", lines=True)
        elif return_as == "dict":
            return df.to_dict(orient="records")
        else:
            raise ValueError(f"Invalid return_as value: {return_as}")

    except Exception as e:
        raise IOError(f"Error reading CSV file: {e}") from e


def read_json(
    filepath: str,
    orient: Optional[str] = None,
    lines: bool = False,
    chunk_size: Optional[int] = None,
    return_as: str = "dataframe",
    **kwargs: Any,
) -> Union[DataFrame, pd.io.json._json.JsonReader]:
    """
    Read JSON file into DataFrame.

    Args:
        filepath: Path to JSON file.
        orient: JSON format specification.
        lines: Read as JSON lines format.
        chunk_size: Number of lines per chunk.
        return_as: Format to return ('dataframe', 'json', 'jsonl', 'dict').
        **kwargs: Additional pandas.read_json arguments.

    Returns:
        Data in specified format.

    Example:
        >>> df = read_json('data.json', orient='records')
    """
    try:
        if chunk_size:
            return pd.read_json(
                filepath,
                orient=orient,
                lines=lines,
                chunksize=chunk_size,
                **kwargs,
            )
        df = pd.read_json(filepath, orient=orient, lines=lines, **kwargs)
        df = to_df(df)

        if return_as == "dataframe":
            return df
        elif return_as == "json":
            return df.to_json(orient="records")
        elif return_as == "jsonl":
            return df.to_json(orient="records", lines=True)
        elif return_as == "dict":
            return df.to_dict(orient="records")
        else:
            raise ValueError(f"Invalid return_as value: {return_as}")

    except Exception as e:
        raise IOError(f"Error reading JSON file: {e}") from e


def to_csv(
    input_: Any,
    /,
    *,
    directory: Union[str, Path],
    filename: str,
    timestamp: bool = False,
    random_hash_digits: int = 0,
    drop_how: str = "all",
    drop_kwargs: Optional[Dict[str, Any]] = None,
    reset_index: bool = True,
    concat_kwargs: Optional[Dict[str, Any]] = None,
    df_kwargs: Optional[Dict[str, Any]] = None,
    path_kwargs: Optional[Dict[str, Any]] = None,
    verbose: bool = False,
) -> None:
    """
    Save data as CSV file.

    Args:
        input_: Data to save.
        directory: Save directory.
        filename: Output filename.
        timestamp: Add timestamp to filename.
        random_hash_digits: Add random hash to filename.
        drop_how: NA handling method.
        drop_kwargs: Additional dropna() arguments.
        reset_index: Reset DataFrame index.
        concat_kwargs: Additional concat() arguments.
        df_kwargs: Additional to_df() arguments.
        path_kwargs: Additional path creation arguments.
        verbose: Print save path.

    Example:
        >>> to_csv(data, directory='output', filename='data')
    """
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
    directory: Union[str, Path],
    filename: str,
    timestamp: bool = False,
    random_hash_digits: int = 0,
    drop_how: str = "all",
    drop_kwargs: Optional[Dict[str, Any]] = None,
    reset_index: bool = True,
    concat_kwargs: Optional[Dict[str, Any]] = None,
    df_kwargs: Optional[Dict[str, Any]] = None,
    path_kwargs: Optional[Dict[str, Any]] = None,
    verbose: bool = False,
) -> None:
    """
    Save data as Excel file.

    Args:
        input_: Data to save.
        directory: Save directory.
        filename: Output filename.
        timestamp: Add timestamp to filename.
        random_hash_digits: Add random hash to filename.
        drop_how: NA handling method.
        drop_kwargs: Additional dropna() arguments.
        reset_index: Reset DataFrame index.
        concat_kwargs: Additional concat() arguments.
        df_kwargs: Additional to_df() arguments.
        path_kwargs: Additional path creation arguments.
        verbose: Print save path.

    Example:
        >>> to_excel(data, directory='output', filename='data')
    """
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


def _list_to_df(
    input_: List,
    /,
    *,
    drop_how: str = "all",
    drop_kwargs: Optional[Dict] = None,
    reset_index: bool = True,
    concat_kwargs: Optional[Dict] = None,
    **kwargs: Any,
) -> DataFrame:
    """Helper function to convert list to DataFrame."""
    if not input_:
        return DataFrame()

    if not isinstance(input_[0], (DataFrame, Series, NDFrame)):
        if drop_kwargs is None:
            drop_kwargs = {}
        try:
            df = DataFrame(input_, **kwargs)
            if "thresh" not in drop_kwargs:
                drop_kwargs["how"] = drop_how
            df = df.dropna(**drop_kwargs)
            return df.reset_index(drop=True) if reset_index else df
        except Exception as e:
            raise ValueError(
                f"Error converting input_ to DataFrame: {e}"
            ) from e

    if drop_kwargs is None:
        drop_kwargs = {}
    try:
        config = (concat_kwargs or {}).copy()
        config.pop("axis", None)
        df = concat(
            input_,
            axis=1 if all(isinstance(i, Series) for i in input_) else 0,
            **(concat_kwargs or {}),
        )
    except Exception as e1:
        try:
            input_ = to_list(input_, dropna=True, flatten=True)
            df = input_[0]
            if len(input_) > 1:
                for i in input_[1:]:
                    df = concat([df, i], **(concat_kwargs or {}))
        except Exception as e2:
            raise ValueError(
                f"Error converting input_ to DataFrame: {e1}, {e2}"
            ) from e2

    drop_kwargs["how"] = drop_how
    df.dropna(**drop_kwargs, inplace=True)
    return df.reset_index(drop=True) if reset_index else df


def general_to_df(
    input_: Any,
    /,
    *,
    drop_how: str = "all",
    drop_kwargs: Optional[Dict[str, Any]] = None,
    reset_index: bool = True,
    **kwargs: Any,
) -> DataFrame:
    """Helper function for general DataFrame conversion."""
    try:
        return _general_to_df(
            input_,
            drop_how=drop_how,
            drop_kwargs=drop_kwargs,
            reset_index=reset_index,
            **kwargs,
        )
    except ValueError:
        try:
            _d = to_dict(input_)
            return _general_to_df(
                _d,
                drop_how=drop_how,
                drop_kwargs=drop_kwargs,
                reset_index=reset_index,
                **kwargs,
            )
        except ValueError:
            raise ValueError("Error converting input_ to DataFrame") from None


def _general_to_df(
    input_: Any,
    /,
    *,
    drop_how: str = "all",
    drop_kwargs: Optional[Dict[str, Any]] = None,
    reset_index: bool = True,
    **kwargs: Any,
) -> DataFrame:
    """Internal helper for DataFrame conversion."""
    if drop_kwargs is None:
        drop_kwargs = {}

    try:
        df = DataFrame(input_, **kwargs)
        if "thresh" not in drop_kwargs:
            drop_kwargs["how"] = drop_how
        df = df.dropna(**drop_kwargs)
        return df.reset_index(drop=True) if reset_index else df
    except Exception as e:
        raise ValueError(f"Error converting input_ to DataFrame: {e}") from e


def extend_dataframe(
    dataframes: Sequence[pd.DataFrame],
    unique_col: str = "node_id",
    keep: Optional[Union[str, bool]] = "first",
    ignore_index: bool = False,
    sort: bool = False,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Merges multiple DataFrames while ensuring no duplicate entries based on a
    specified unique column.

    Args:
        dataframes: List of DataFrames to merge, with the first being primary.
        unique_col: Column name to check for duplicate entries.
        keep: Which duplicates to keep. 'first' keeps first occurrence,
              'last' keeps last occurrence, and False drops all duplicates.
        ignore_index: If True, resulting axis will be labeled 0, 1, …, n - 1.
        sort: If True, sort join keys lexicographically.
        **kwargs: Additional arguments for drop_duplicates.

    Returns:
        DataFrame combined from inputs with duplicates removed.

    Raises:
        ValueError: If all DataFrames empty or error in extending.

    Example:
        >>> df1 = pd.DataFrame({'node_id': [1, 2], 'value': ['a', 'b']})
        >>> df2 = pd.DataFrame({'node_id': [2, 3], 'value': ['c', 'd']})
        >>> extend_dataframe([df1, df2], keep='last', ignore_index=True)
           node_id value
        0       1     a
        1       2     c
        2       3     d
    """
    try:
        if all(df.empty for df in dataframes):
            raise ValueError("All input DataFrames are empty.")

        combined = pd.concat(dataframes, ignore_index=ignore_index, sort=sort)
        result = combined.drop_duplicates(
            subset=[unique_col], keep=keep, **kwargs
        )

        if result.empty:
            raise ValueError("No data left after removing duplicates.")

        return to_df(result)

    except Exception as e:
        raise ValueError(f"Error in extending DataFrames: {e}") from e


def remove_rows(
    df: pd.DataFrame,
    rows: Union[int, slice, List[int]],
    from_end: bool = False,
    reset_index: bool = False,
) -> pd.DataFrame:
    """
    Removes specified rows from a DataFrame.

    Args:
        df: DataFrame from which to remove rows.
        rows: Row(s) to remove. Can be integer, slice, or list of integers.
        from_end: If True, count rows from end of DataFrame.
        reset_index: If True, reset index after removing rows.

    Returns:
        DataFrame with specified rows removed.

    Raises:
        ValueError: If specified rows are invalid.

    Example:
        >>> df = pd.DataFrame({'A': range(10)})
        >>> remove_rows(df, [0, 2, 4], reset_index=True)
           A
        0  1
        1  3
        2  5
        3  6
        4  7
        5  8
        6  9
    """
    if df.empty:
        return df.copy()

    if isinstance(rows, int):
        rows = [rows]
    elif isinstance(rows, slice):
        rows = list(range(*rows.indices(len(df))))

    if from_end:
        rows = [len(df) - 1 - r for r in rows]

    try:
        result = df.drop(df.index[rows])
    except IndexError as e:
        raise ValueError(f"Invalid row selection: {e}") from e

    if reset_index:
        result = result.reset_index(drop=True)

    return to_df(result)


def replace_keywords(
    df: pd.DataFrame,
    keyword: Union[str, Dict[str, str]],
    replacement: Optional[str] = None,
    *,
    column: Union[str, List[str]] = "content",
    case_sensitive: bool = False,
    regex: bool = False,
    inplace: bool = False,
) -> Optional[pd.DataFrame]:
    """
    Replace occurrences of keywords with replacement string(s) in DataFrame column(s).

    Args:
        df: DataFrame to modify.
        keyword: Keyword to replace. String or dict of {old: new} pairs.
        replacement: String to replace keyword with. Ignored if keyword is dict.
        column: Column(s) for replacement. String or list of strings.
        case_sensitive: If True, do case-sensitive replacement.
        regex: If True, treat keywords as regular expressions.
        inplace: If True, modify DataFrame in place.

    Returns:
        Modified DataFrame if not inplace, None otherwise.

    Example:
        >>> df = pd.DataFrame({'content': ['apple pie', 'banana split']})
        >>> replace_keywords(
        ...     df,
        ...     {'pie': 'tart', 'split': 'smoothie'},
        ...     column='content'
        ... )
           content
        0  apple tart
        1  banana smoothie
    """
    df_ = df if inplace else df.copy()

    if isinstance(column, str):
        column = [column]

    if isinstance(keyword, dict):
        for col in column:
            df_[col] = df_[col].replace(
                to_replace=keyword,
                regex=regex,
                case=case_sensitive,
            )
    else:
        for col in column:
            df_[col] = df_[col].replace(
                to_replace=keyword,
                value=replacement,
                regex=regex,
                case=case_sensitive,
            )

    if inplace:
        return None
    return to_df(df_)


def search_dataframe_keywords(
    df: pd.DataFrame,
    keywords: Union[str, List[str]],
    *,
    column: Union[str, List[str]] = "content",
    case_sensitive: bool = False,
    reset_index: bool = False,
    dropna: bool = False,
    regex: bool = False,
    match_all: bool = False,
) -> pd.DataFrame:
    """
    Filter DataFrame for rows where column(s) contain given keywords.

    Args:
        df: DataFrame to search through.
        keywords: Keyword(s) to search for.
        column: Column(s) to search in. String or list of strings.
        case_sensitive: Whether search should be case-sensitive.
        reset_index: Whether to reset index after filtering.
        dropna: Whether to drop NA values before searching.
        regex: If True, treat keywords as regular expressions.
        match_all: If True, all keywords must be present for a match.

    Returns:
        Filtered DataFrame containing matching rows.

    Example:
        >>> df = pd.DataFrame({'content': ['apple pie', 'banana split']})
        >>> search_dataframe_keywords(df, ['pie', 'cherry'], match_all=True)
           content
        2  cherry pie
    """
    try:
        if dropna:
            df = df.dropna(
                subset=[column] if isinstance(column, str) else column
            )

        if isinstance(keywords, str):
            keywords = [keywords]

        if isinstance(column, str):
            column = [column]

        mask = pd.DataFrame(index=df.index)
        for col in column:
            col_mask = pd.Series(False, index=df.index)
            for keyword in keywords:
                keyword_mask = df[col].str.contains(
                    keyword, case=case_sensitive, regex=regex, na=False
                )
                col_mask = col_mask | keyword_mask
            mask[col] = col_mask

        final_mask = mask.all(axis=1) if match_all else mask.any(axis=1)

        result = df[final_mask]

        if reset_index:
            result = result.reset_index(drop=True)

        return to_df(result)

    except Exception as e:
        raise ValueError(f"Error searching DataFrame: {e}") from e


def update_cells(
    df: pd.DataFrame,
    updates: Dict[Tuple[Union[int, str], Union[int, str]], Any],
    create_missing: bool = False,
) -> pd.DataFrame:
    """
    Update multiple cells in a DataFrame based on a dictionary of updates.

    Args:
        df: DataFrame to update.
        updates: Dictionary where keys are (row, column) tuples and values
                are the new values. Rows and columns can be specified by
                integer position or label.
        create_missing: If True, create new columns if they don't exist.

    Returns:
        Updated DataFrame.

    Raises:
        KeyError: If specified row/column doesn't exist and create_missing
                 is False.

    Example:
        >>> df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        >>> updates = {
        ...     (0, 'A'): 10,
        ...     (1, 'B'): 40,
        ...     (0, 'C'): 100
        ... }
        >>> update_cells(df, updates, create_missing=True)
           A   B    C
        0  10   3  100
        1   2  40  NaN
    """
    try:
        df_copy = df.copy()

        for (row, col), value in updates.items():
            try:
                if isinstance(col, str) and col not in df_copy.columns:
                    if create_missing:
                        df_copy[col] = None
                    else:
                        raise KeyError(f"Column '{col}' does not exist")

                df_copy.loc[row, col] = value

            except KeyError as e:
                if not create_missing:
                    raise KeyError(f"Invalid row or column: {e}") from e
                continue

        return to_df(df_copy)

    except Exception as e:
        raise ValueError(f"Error updating DataFrame cells: {e}") from e


# Update __all__ to include new functions
__all__ = [
    "to_df",
    "read_csv",
    "read_json",
    "to_csv",
    "to_excel",
    "general_to_df",
    "extend_dataframe",
    "remove_rows",
    "replace_keywords",
    "search_dataframe_keywords",
    "update_cells",
]
