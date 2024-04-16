from __future__ import annotations

from datetime import date, datetime, time
from json import JSONEncoder as _JSONEncoder
from json import dump as _dump
from json import dumps as _dumps
from json import load, loads  # noqa: F401
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Self, TextIO


def _serialize_obj(obj: Any) -> str:
    if isinstance(obj, datetime | date | time):
        return obj.isoformat()

    raise TypeError


def _serialize_key(key: Any) -> Any:
    if isinstance(key, datetime | date | time):
        return key.isoformat()
    return key


class _SerializeKeysJSONEncoder(_JSONEncoder):
    def encode(self: Self, obj: Any) -> Any:
        if isinstance(obj, dict):
            obj = {_serialize_key(key): value for key, value in obj.items()}
        return super().encode(obj)


INDENT = 4


def dump(
    obj: Any,
    fp: TextIO,
    *,
    default: Callable[[Any], str] = _serialize_obj,
    cls: type[_JSONEncoder] = _SerializeKeysJSONEncoder,
    indent: int = INDENT,
    **kwargs: Any,
) -> None:
    return _dump(obj, fp, default=default, cls=cls, indent=indent, **kwargs)


def dumps(
    obj: Any,
    *,
    default: Callable[[Any], str] = _serialize_obj,
    cls: type[_JSONEncoder] = _SerializeKeysJSONEncoder,
    indent: int = INDENT,
    **kwargs: Any,
) -> str:
    return _dumps(obj, default=default, cls=cls, indent=indent, **kwargs)
