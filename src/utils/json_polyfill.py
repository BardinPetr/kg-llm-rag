import json
from json import JSONEncoder


class StrFallbackEncoder(JSONEncoder):
    """
    Custom JSON encoder that falls back to __str__() for non-serializable objects.
    """

    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


_original_dumps = json.dumps
_original_dump = json.dump


def patched_dumps(obj, *, skipkeys=False, ensure_ascii=True, check_circular=True,
                  allow_nan=True, cls=None, indent=None, separators=None,
                  default=None, sort_keys=False, **kw):
    if cls is None:
        cls = StrFallbackEncoder

    return _original_dumps(
        obj, skipkeys=skipkeys, ensure_ascii=ensure_ascii,
        check_circular=check_circular, allow_nan=allow_nan,
        cls=cls, indent=indent, separators=separators,
        default=default, sort_keys=sort_keys, **kw
    )


def patched_dump(obj, fp, *, skipkeys=False, ensure_ascii=True, check_circular=True,
                 allow_nan=True, cls=None, indent=None, separators=None,
                 default=None, sort_keys=False, **kw):
    if cls is None:
        cls = StrFallbackEncoder

    return _original_dump(
        obj, fp, skipkeys=skipkeys, ensure_ascii=ensure_ascii,
        check_circular=check_circular, allow_nan=allow_nan,
        cls=cls, indent=indent, separators=separators,
        default=default, sort_keys=sort_keys, **kw
    )


def install_json():
    json.dumps = patched_dumps
    json.dump = patched_dump
    json.JSONEncoder = StrFallbackEncoder
