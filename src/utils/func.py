import statistics
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from time import perf_counter
from typing import *

import cloudpickle
import wrapt

from src.utils.file import anything_hash, do_hash


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
    import sys
    sys.stdout.flush()
    start = time.perf_counter()
    name = decorator_get_wrapped_name(wrapped, instance)
    print(f"[{name}] BEGIN")

    result = wrapped(*args, **kwargs)

    delta_s = time.perf_counter() - start
    print(f"[{name}] END time={delta_s:.4f}s")
    return result


@contextmanager
def stat():
    times = defaultdict(list)

    @contextmanager
    def measure(name: str):
        start = perf_counter()
        yield
        times[name].append((perf_counter() - start) * 1000)

    yield measure

    for name, vals in times.items():
        mean = statistics.mean(vals)
        stdev = statistics.stdev(vals) if len(vals) > 1 else 0
        print(f"[{name}]: #{len(vals)} time={mean:.3f}±{stdev:.3f}ms total={sum(vals):.1f}ms")


def default_cache_key_fn(*args, **kwargs) -> str:
    parts = [anything_hash(a) for a in args]
    parts += [f"{k}={anything_hash(v)}" for k, v in sorted(kwargs.items())]
    return ":".join(parts)


def disk_cache(cache_dir: str, key_fn: Callable = default_cache_key_fn):
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        cache_root = Path(cache_dir)
        cache_root.mkdir(parents=True, exist_ok=True)
        raw_key = key_fn(*args, **kwargs)
        path = cache_root / do_hash(raw_key)
        if path.exists():
            with path.open("rb") as fh:
                return cloudpickle.load(fh)
        result = wrapped(*args, **kwargs)
        with path.open("wb") as fh:
            cloudpickle.dump(result, fh)
        return result

    def decorator(func):
        return wrapper(func)

    return decorator
