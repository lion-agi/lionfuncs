from inspect import isclass
from typing import get_args

from pydantic import BaseModel


def break_down_annotation(model: type[BaseModel]):

    def _ispydantic_model(x):
        return isclass(x) and issubclass(x, BaseModel)

    if not _ispydantic_model(model):
        return model

    out = {}
    for k, v in model.__annotations__.items():
        if _ispydantic_model(v):
            out[k] = break_down_annotation(v)
        elif "list" in str(v) and get_args(v):
            v = get_args(v)[0]
            if _ispydantic_model(v):
                v = break_down_annotation(v)
            out[k] = [v]
        else:
            out[k] = v
    return out
