from typing import Any

from pandas import DataFrame, Series, concat
from pandas.core.generic import NDFrame

from lionfuncs.data_handlers.to_dict import to_dict
from lionfuncs.data_handlers.to_list import to_list


def to_df(
    input_: Any,
    /,
    *,
    drop_how: str = "all",
    drop_kwargs: dict | None = None,
    reset_index: bool = True,
    concat_kwargs: dict | None = None,
    **kwargs,
) -> DataFrame:
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


def general_to_df(
    input_: Any,
    /,
    *,
    drop_how: str = "all",
    drop_kwargs: dict[str, Any] | None = None,
    reset_index: bool = True,
    **kwargs: Any,
) -> DataFrame:

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
    drop_kwargs: dict[str, Any] | None = None,
    reset_index: bool = True,
    **kwargs: Any,
) -> DataFrame:
    if drop_kwargs is None:
        drop_kwargs = {}

    try:
        df: DataFrame = DataFrame(input_, **kwargs)

        if "thresh" not in drop_kwargs:
            drop_kwargs["how"] = drop_how
        df = df.dropna(**drop_kwargs)
        return df.reset_index(drop=True) if reset_index else df
    except Exception as e:
        raise ValueError(f"Error converting input_ to DataFrame: {e}") from e


def _list_to_df(
    input_: list,
    /,
    *,
    drop_how: str = "all",
    drop_kwargs: dict | None = None,
    reset_index: bool = True,
    concat_kwargs: dict | None = None,
    **kwargs,
) -> DataFrame:
    if not input_:
        return DataFrame()

    if not isinstance(input_[0], (DataFrame, Series, NDFrame)):
        if drop_kwargs is None:
            drop_kwargs = {}
        try:
            df: DataFrame = DataFrame(input_, **kwargs)
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
        config = concat_kwargs.copy()
        config.pop("axis", None)
        df = concat(
            input_,
            axis=1 if all(isinstance(i, Series) for i in input_) else 0,
            **concat_kwargs,
        )
    except Exception as e1:
        try:
            input_ = to_list(input_, dropna=True, flatten=True)
            df = input_[0]
            if len(input_) > 1:
                for i in input_[1:]:
                    df = concat([df, i], **concat_kwargs)
        except Exception as e2:
            raise ValueError(
                f"Error converting input_ to DataFrame: {e1}, {e2}"
            ) from e2

    drop_kwargs["how"] = drop_how
    df.dropna(**drop_kwargs, inplace=True)
    return df.reset_index(drop=True) if reset_index else df
