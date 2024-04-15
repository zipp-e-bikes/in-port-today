from __future__ import annotations
from json import dump as _dump, dumps as _dumps, JSONEncoder as _JSONEncoder
from json import loads, load  # noqa: F401
from typing import TYPE_CHECKING
from datetime import datetime, date, time

if TYPE_CHECKING:
    from typing import Any, TextIO


def _serialize_obj(obj: Any) -> str:
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()

    raise TypeError


def _serialize_key(key: Any) -> Any:
    if isinstance(key, (datetime, date, time)):
        return key.isoformat()
    return key


class _SerializeKeysJSONEncoder(_JSONEncoder):
    def encode(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            obj = {_serialize_key(key): value for key, value in obj.items()}
        return super().encode(obj)


INDENT = 4


def dump(
    obj: Any,
    fp: TextIO,
    *,
    default=_serialize_obj,
    cls=_SerializeKeysJSONEncoder,
    indent=INDENT,
    **kwargs,
) -> None:
    return _dump(obj, fp, default=default, cls=cls, indent=indent, **kwargs)


def dumps(
    obj: Any,
    *,
    default=_serialize_obj,
    cls=_SerializeKeysJSONEncoder,
    indent=INDENT,
    **kwargs,
) -> str:
    return _dumps(obj, default=default, cls=cls, indent=indent, **kwargs)
