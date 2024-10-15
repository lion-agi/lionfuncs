from typing import Annotated, Any

from pydantic import (
    BaseModel,
    Field,
    create_model,
    field_serializer,
    field_validator,
)
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from lionfuncs.ln_undefined import LN_UNDEFINED

NAMED_FIELD = Annotated[str, Field(..., alias="field")]


class MutableModel(BaseModel):

    extra_fields: dict[str, Any] = Field(default_factory=dict)

    @field_serializer("extra_fields")
    def _serialize_extra_fields(
        self,
        value: dict[str, FieldInfo],
    ) -> dict[str, Any]:
        """Custom serializer for extra fields."""
        output_dict = {}
        for k in value.keys():
            k_value = self.__dict__.get(k)
            output_dict[k] = k_value
        return output_dict

    @field_validator("extra_fields")
    def _validate_extra_fields(cls, value: Any) -> dict[str, FieldInfo]:
        """Custom validator for extra fields."""
        if not isinstance(value, dict):
            raise ValueError("Extra fields must be a dictionary")

        out_ = {}
        for k, v in value.items():
            out_[k] = Field(**v) if isinstance(v, dict) else v

        return out_

    @property
    def all_fields(self) -> dict[str, FieldInfo]:
        return {**self.model_fields, **self.extra_fields}

    def add_field(
        self,
        field_name: NAMED_FIELD,
        /,
        value: Any = LN_UNDEFINED,
        annotation: Any = LN_UNDEFINED,
        field_obj: FieldInfo = LN_UNDEFINED,
        **kwargs,
    ) -> None:
        if field_name in self.all_fields:
            raise ValueError(f"Field '{field_name}' already exists")

        self.update_field(
            field_name,
            value=value,
            annotation=annotation,
            field_obj=field_obj,
            **kwargs,
        )

    def update_field(
        self,
        field_name: NAMED_FIELD,
        /,
        value: Any = LN_UNDEFINED,
        annotation: Any = LN_UNDEFINED,
        field_obj: FieldInfo | Any = LN_UNDEFINED,
        **kwargs,
    ) -> None:

        # pydanitc Field object cannot have both default and default_factory
        if "default" in kwargs and "default_factory" in kwargs:
            raise ValueError(
                "Cannot provide both 'default' and 'default_factory'",
            )

        # handle field_obj
        if field_obj is not LN_UNDEFINED:
            if not isinstance(field_obj, FieldInfo):
                raise ValueError(
                    "Invalid field_obj, should be a pydantic FieldInfo object"
                )
            self.extra_fields[field_name] = field_obj

        # handle kwargs
        if kwargs:
            if field_name in self.all_fields:  # existing field
                for k, v in kwargs.items():
                    self.field_setattr(field_name, k, v)
            else:
                self.extra_fields[field_name] = Field(**kwargs)

        # handle no explicit defined field
        if field_obj is LN_UNDEFINED and not kwargs:
            if field_name not in self.all_fields:
                self.extra_fields[field_name] = Field()

        field_obj = self.all_fields[field_name]

        # handle annotation
        if annotation is not LN_UNDEFINED:
            field_obj.annotation = annotation
        if not field_obj.annotation:
            field_obj.annotation = Any

        # handle value
        if value is LN_UNDEFINED:
            if getattr(self, field_name, LN_UNDEFINED) is not LN_UNDEFINED:
                value = getattr(self, field_name)

            elif getattr(field_obj, "default") is not PydanticUndefined:
                value = field_obj.default

            elif getattr(field_obj, "default_factory"):
                value = field_obj.default_factory()

        setattr(self, field_name, value)

    def field_setattr(
        self,
        field_name: str,
        attr: Any,
        value: Any,
        /,
    ) -> None:
        """Set the value of a field attribute."""
        all_fields = self.all_fields
        if field_name not in all_fields:
            raise KeyError(f"Field {field_name} not found in object fields.")
        field_obj = all_fields[field_name]
        if hasattr(field_obj, attr):
            setattr(field_obj, attr, value)
        else:
            if not isinstance(field_obj.json_schema_extra, dict):
                field_obj.json_schema_extra = {}
            field_obj.json_schema_extra[attr] = value

    def field_hasattr(
        self,
        field_name: str,
        attr: str,
        /,
    ) -> bool:
        """Check if a field has a specific attribute."""
        all_fields = self.all_fields
        if field_name not in all_fields:
            raise KeyError(f"Field {field_name} not found in object fields.")
        field_obj = all_fields[field_name]
        if hasattr(field_obj, attr):
            return True
        elif isinstance(field_obj.json_schema_extra, dict):
            if field_name in field_obj.json_schema_extra:
                return True
        else:
            return False

    def field_getattr(
        self,
        field_name: str,
        attr: str,
        default: Any = LN_UNDEFINED,
        /,
    ) -> Any:
        """Get the value of a field attribute."""
        if str(attr).strip("s").lower() == "annotation":
            return self._field_annotation(field_name)

        all_fields = self.all_fields
        if field_name not in all_fields:
            raise KeyError(f"Field {field_name} not found in object fields.")
        field_obj = all_fields[field_name]

        # check fieldinfo attr

        value = getattr(field_obj, attr, LN_UNDEFINED)
        if value is not LN_UNDEFINED:
            return value
        else:
            if isinstance(field_obj.json_schema_extra, dict):
                value = field_obj.json_schema_extra.get(attr, LN_UNDEFINED)
                if value is not LN_UNDEFINED:
                    return value

        # undefined attr
        if default is not LN_UNDEFINED:
            return default
        else:
            raise AttributeError(
                f"field {field_name} has no attribute {attr}",
            )

    def create_model(
        self, model_name: str = None, **kwargs
    ) -> type[BaseModel]:
        """kwargs are name: field_info pairs"""
        config = self.all_fields
        config.update(kwargs)
        config.pop("extra_fields")
        for k, v in self.all_fields.items():
            config[k] = (v.annotation, v)
        model_name = model_name or f"Dynamic{self.__class__.__name__}"
        return create_model(model_name, **config)

    @classmethod
    def new_model(cls, model_name: str, **kwargs) -> type[BaseModel]:
        config = cls.model_fields
        config.update(kwargs)
        config.pop("extra_fields")
        for k, v in config:
            config[k] = (v.annotation, v)
        model_name = model_name or f"Dynamic{cls.__name__}"
        return create_model(model_name, **config)
