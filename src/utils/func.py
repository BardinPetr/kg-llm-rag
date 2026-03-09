import threading
import time
from functools import wraps
from typing import Callable, cast

import wrapt


def rate_limited[T, **P](max_per_second: int) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(fn: Callable[P, T]) -> Callable[P, T]:
        lock = threading.RLock()
        min_interval = 1.0 / max_per_second
        last_time_called = 0.0

        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            with lock:
                nonlocal last_time_called
                elapsed = time.perf_counter() - last_time_called
                left_to_wait = min_interval - elapsed
                if left_to_wait > 0:
                    time.sleep(left_to_wait)

                last_time_called = time.perf_counter()
                return fn(*args, **kwargs)

        return cast(Callable[P, T], wrapper)

    return decorator


def decorator_get_wrapped_name(func, instance):
    pfx = ""
    if instance:
        pfx = f"{instance.__class__.__name__}."
    return f"{pfx}{func.__name__}"


@wrapt.decorator
def logged(wrapped, instance, args, kwargs):
    import time
    print("1")
    import sys
    sys.stdout.flush()
    start = time.perf_counter()
    name = decorator_get_wrapped_name(wrapped, instance)
    print(f"[{name}] BEGIN")

    result = wrapped(*args, **kwargs)

    delta_s = time.perf_counter() - start
    print(f"[{name}] END time={delta_s:.4f}s")
    return result
