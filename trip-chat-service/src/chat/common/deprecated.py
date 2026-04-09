import warnings
from typing import Any, Callable


def deprecated(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            f"{func.__name__} is deprecated and will be removed in future versions.",
            DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    return wrapper
