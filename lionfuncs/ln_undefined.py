from typing import Literal


class LionUndefinedType:
    def __init__(self) -> None:
        self.undefined = True

    def __bool__(self) -> Literal[False]:
        return False

    def __deepcopy__(self, memo):
        # Ensure LN_UNDEFINED is universal
        return self

    def __repr__(self) -> Literal["LN_UNDEFINED"]:
        return "LN_UNDEFINED"

    __slots__ = ["undefined"]


LN_UNDEFINED = LionUndefinedType()

__all__ = ["LN_UNDEFINED", "LionUndefinedType"]
