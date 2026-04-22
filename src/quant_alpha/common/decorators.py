import functools
from typing import Any, Callable, TypeVar

from quant_alpha.common.config import settings

F = TypeVar("F", bound=Callable[..., Any])


def requires_confirmation(func: F) -> F:
    """실제 자금 관련 함수에 적용. live 모드에서만 사용자 확인을 요구한다."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if settings.is_live:
            answer = input(f"[LIVE] {func.__name__} 실행 확인 (yes/no): ")
            if answer.strip().lower() != "yes":
                raise RuntimeError(f"{func.__name__} 실행이 취소되었습니다.")
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
