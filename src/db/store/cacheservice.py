from pathlib import Path
from typing import *

import cloudpickle
import wrapt
from langchain_community.storage import RedisStore

from utils.config import sys_cfg
from utils.file import do_hash, anything_hash

kv_store = RedisStore(redis_url=sys_cfg.redis.conn)


def _key_func(bucket, key_fn):
    f = do_hash if key_fn is None else key_fn
    return lambda x: f"{bucket}/{f(x)}"


def cache_get[K](keys: List[K], bucket: str = "default", key=None) -> Tuple[Dict[K, Any], List[K]]:
    kfn = _key_func(bucket, key)
    enc_keys = [kfn(i) for i in keys]
    loaded = kv_store.mget(enc_keys)
    hit, miss = dict(), set()
    for k, res in zip(keys, loaded):
        if res is None:
            miss.add(k)
        else:
            hit[k] = cloudpickle.loads(res)
    return hit, list(miss)


def cache_put(kv: Dict, bucket: str = "default", key=None, value_transform=None):
    if value_transform is None:
        value_transform = lambda x: cloudpickle.dumps(x)
    kfn = _key_func(bucket, key)
    kv_store.mset([
        (kfn(k), value_transform(v))
        for k, v in kv.items()
    ])


def cache_iget(key: Any, bucket: str = "default") -> Optional[Any]:
    res, _ = cache_get([key], bucket)
    return res.get(key, None)


def cache_iput(key: Any, value: Any, bucket: str = "default") -> Optional[Any]:
    cache_put({key: value}, bucket)


def default_cache_key_fn(*args, **kwargs) -> str:
    parts = [anything_hash(a) for a in args]
    parts += [f"{k}={anything_hash(v)}" for k, v in sorted(kwargs.items())]
    return ":".join(parts)


def cached(cache_dir: str = None, cache_bucket: str = "fc", key_fn: Callable = default_cache_key_fn):
    assert (cache_dir is None) ^ (cache_bucket is None)

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        raw_key = do_hash(key_fn(*args, **kwargs))

        if cache_dir:
            cache_root = Path(cache_dir)
            cache_root.mkdir(parents=True, exist_ok=True)
            path = cache_root / raw_key
            if path.exists():
                with path.open("rb") as fh:
                    return cloudpickle.load(fh)
            result = wrapped(*args, **kwargs)
            with path.open("wb") as fh:
                cloudpickle.dump(result, fh)
            return result
        else:
            if obj := cache_iget(raw_key, cache_bucket):
                return obj
            result = wrapped(*args, **kwargs)
            cache_iput(raw_key, result, cache_bucket)
            return result

    return wrapper


def move_cache(dir_path: str, bucket):
    data = {
        i.name: i.read_bytes()
        for i in Path(dir_path).iterdir()
    }
    cache_put(data, bucket, value_transform=lambda x: x)
