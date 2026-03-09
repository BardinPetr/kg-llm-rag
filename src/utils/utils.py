import hashlib
import os

from networkx.classes.filters import show_nodes
from tqdm.contrib.concurrent import process_map


def pmap(fn, arr):
    return process_map(fn, arr, max_workers=os.cpu_count())


def fmap(x):
    return [float(i) for i in x]


def imap(x):
    return [int(i) for i in fmap(x)]


def imapn(x):
    return [[int(float(j)) for j in i] for i in x]

def flist(x, digits=7):
    return " ".join(str(round(i, digits)) for i in x)

def dict_drop_key(d, keys):
    return {k: v for k, v in d.items() if k not in keys}


def amul(arr, x):
    return [x * i for i in arr]


def zmul(arr, arr2):
    return [i * j for i, j in zip(arr, arr2)]


def zdiv(arr, arr2):
    return [i / j for i, j in zip(arr, arr2)]

def xhash(x):
    return hashlib.md5(str(x).encode()).hexdigest()


def hsv2rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)

def associate(x, by_field=None, key_transform = lambda x: x, value_transform=lambda x: x):
    return {
        (i[by_field] if by_field else key_transform(i)): value_transform(i)
        for i in x
    }
