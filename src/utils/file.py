import hashlib
import json
import re
from pathlib import Path

import cloudpickle


def rd(x: Path | str) -> str:
    return open(str(x)).read()


def rdj(x: Path | str):
    return json.loads(rd(x))


def rdp(x: Path | str):
    return cloudpickle.load(open(str(x), "rb"))


def wr(x: Path | str, data):
    if isinstance(x, str):
        x = Path(x)
    x.parent.mkdir(parents=True, exist_ok=True)
    with open(str(x), "w") as f:
        f.write(str(data))


def wrp(x: Path | str, data):
    if isinstance(x, str):
        x = Path(x)
    x.parent.mkdir(parents=True, exist_ok=True)
    with open(str(x), "wb") as f:
        cloudpickle.dump(data, f)


def wrj(x: Path | str, data):
    wr(x, json.dumps(data))


def ftmp() -> Path:
    pass


def do_file_hash(path: str | Path) -> str:
    path = Path(path)
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def do_hash(value: str | bytes) -> str:
    value = value.encode("utf-8") if isinstance(value, str) else bytes(value)
    return hashlib.md5(value).hexdigest()


path_re = re.compile(r'^(?:\.{0,2}/)?(?:[a-zA-Z0-9._-]+/)*[a-zA-Z0-9._-]*$')


def anything_hash(arg) -> str:
    if isinstance(arg, Path) and arg.is_file():
        return do_file_hash(arg)

    if isinstance(arg, str) and path_re.match(arg):
        try:
            resolved = Path(arg).resolve()
            if resolved.is_file():
                return do_file_hash(resolved)
        except TypeError:
            pass

    try:
        return do_hash(cloudpickle.dumps(arg))
    except:
        pass

    return do_hash(str(arg))
