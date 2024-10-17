from pydantic import BaseModel, ConfigDict
from pydantic import create_model as _create_model


def new_model(
    base: BaseModel,
    model_name=None,
    use_all_fields=False,
    config_dict: ConfigDict = None,
    doc: str | None = None,
    validators: dict = None,
    use_cls_kwargs=False,
    use_base_cls=False,
    **kwargs,
):
    if use_all_fields and hasattr(base, "all_fields"):
        kwargs.update(base.all_fields)
    else:
        kwargs.update(base.model_fields)

    cls_kwargs = {}
    config = {}
    for k, v in kwargs.items():
        config[k] = (v.annotation, v)
        cls_kwargs[k] = getattr(base, k)

    if config_dict:
        config["__config__"] = config_dict
    if doc:
        config["__doc__"] = doc
    if validators:
        config["__validators__"] = validators
    if use_cls_kwargs:
        config["__cls_kwargs__"] = cls_kwargs
    if use_base_cls:
        config["__base__"] = base.__class__

    return _create_model(
        model_name or f"Dynamic{base.__class__.__name__}", **kwargs
    )
