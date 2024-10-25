"""
Pydantic model manipulation utilities for creating and analyzing models.

Features:
- Create new models from existing ones
- Break down model annotations
- Handle nested models
- Type checking utilities
"""

from inspect import isclass
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    create_model,
    field_validator,
)
from pydantic.fields import FieldInfo

T = TypeVar("T", bound=BaseModel)


def new_model(
    base: Union[Type[T], T],
    *,
    model_name: Optional[str] = None,
    use_all_fields: bool = False,
    config_dict: Optional[ConfigDict] = None,
    doc: Optional[str] = None,
    validators: Optional[Dict[str, Callable]] = None,
    use_base_kwargs: bool = False,
    inherit_base: bool = False,
    extra_fields: Optional[Dict[str, Any]] = None,
    field_descriptions: Optional[Dict[str, str]] = None,
    exclude_fields: Optional[List[str]] = None,
    frozen: bool = False,
) -> Type[BaseModel]:
    """
    Create a new Pydantic model based on an existing model with customizations.

    Args:
        base: Base model or instance to derive from.
        model_name: Name for new model. Defaults to f"Dynamic{base.__name__}".
        use_all_fields: If True, includes fields from base.all_fields.
        config_dict: Additional configuration options.
        doc: Docstring for new model.
        validators: Dictionary of field validators.
        use_base_kwargs: If True, includes base class kwargs.
        inherit_base: If True, sets base as parent class.
        extra_fields: Additional fields to add.
        field_descriptions: Dictionary of field descriptions.
        exclude_fields: List of fields to exclude.
        frozen: If True, creates immutable model.

    Returns:
        A new Pydantic model class.

    Example:
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int
        >>> NewUser = new_model(
        ...     User,
        ...     model_name="ExtendedUser",
        ...     extra_fields={"email": (str, ...)}
        ... )
    """
    if not isinstance(base, type) or not issubclass(base, BaseModel):
        if not isinstance(base, BaseModel):
            raise ValueError("base must be a Pydantic model class or instance")
        base = type(base)

    fields = {}
    if use_all_fields and hasattr(base, "all_fields"):
        fields.update(base.all_fields)
    else:
        fields.update(base.model_fields)

    if exclude_fields:
        for field in exclude_fields:
            fields.pop(field, None)

    if extra_fields:
        fields.update(extra_fields)

    if field_descriptions:
        for field_name, description in field_descriptions.items():
            if field_name in fields:
                field_info = fields[field_name]
                if isinstance(field_info, tuple):
                    fields[field_name] = (
                        field_info[0],
                        Field(..., description=description),
                    )
                elif isinstance(field_info, FieldInfo):
                    fields[field_name] = field_info.model_copy(
                        update={"description": description}
                    )

    config = ConfigDict()
    if config_dict:
        config.update(config_dict)
    if frozen:
        config["frozen"] = True

    class_kwargs = {}
    if use_base_kwargs:
        class_kwargs.update(
            {
                k: getattr(base, k)
                for k in base.__dict__
                if not k.startswith("__")
            }
        )

    new_model_name = model_name or f"Dynamic{base.__name__}"
    model: Type[BaseModel] = create_model(
        new_model_name, __base__=base if inherit_base else BaseModel, **fields
    )

    if config:
        model.model_config = config

    if doc:
        model.__doc__ = doc

    if validators:
        for field, validator_func in validators.items():
            setattr(
                model,
                f"validate_{field}",
                field_validator(field)(validator_func),
            )

    for key, value in class_kwargs.items():
        setattr(model, key, value)

    return model


def break_down_pydantic_annotation(
    model: Type[T], max_depth: Optional[int] = None, current_depth: int = 0
) -> Dict[str, Any]:
    """
    Break down Pydantic model type annotations into a dictionary.

    Args:
        model: Pydantic model class to break down.
        max_depth: Maximum recursion depth. None for no limit.
        current_depth: Current recursion depth (internal).

    Returns:
        Dictionary of model's annotation structure.

    Example:
        >>> class SubModel(BaseModel):
        ...     field1: int
        >>> class MainModel(BaseModel):
        ...     sub: SubModel
        ...     items: List[SubModel]
        >>> result = break_down_pydantic_annotation(MainModel)
    """
    if not _is_pydantic_model(model):
        raise TypeError("Input must be a Pydantic model")

    if max_depth is not None and current_depth >= max_depth:
        raise RecursionError("Maximum recursion depth reached")

    out: Dict[str, Any] = {}
    for k, v in model.__annotations__.items():
        origin = get_origin(v)
        if _is_pydantic_model(v):
            out[k] = break_down_pydantic_annotation(
                v, max_depth, current_depth + 1
            )
        elif origin is list:
            args = get_args(v)
            if args and _is_pydantic_model(args[0]):
                out[k] = [
                    break_down_pydantic_annotation(
                        args[0], max_depth, current_depth + 1
                    )
                ]
            else:
                out[k] = [args[0] if args else Any]
        else:
            out[k] = v

    return out


def _is_pydantic_model(x: Any) -> bool:
    """Check if x is a Pydantic model class."""
    return isclass(x) and issubclass(x, BaseModel)


__all__ = [
    "new_model",
    "break_down_pydantic_annotation",
]
