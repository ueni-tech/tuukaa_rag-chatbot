"""
レートリミット雛形。

将来 `slowapi` 等で実装を入れ替える前提で、今は no-op デコレータを提供。
"""

from typing import Callable, TypeVar, Any, cast


F = TypeVar("F", bound=Callable[..., Any])


def rate_limited(_key: str | None = None) -> Callable[[F], F]:
    def wrapper(func: F) -> F:
        return cast(F, func)

    return wrapper
