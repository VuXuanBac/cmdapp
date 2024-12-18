import re
from ..utils import Text, Json

from .sqlite import (
    get_sqlite_converter,
    get_python_converter,
    datetime,
    SUPPORT_DTYPES,
    SQLITE_BUILTIN_DTYPES,
)

TEXT_CONVERTERS = {
    "str": str,
    "telex": Text.convert_to_telex,
    "ascii": Text.convert_to_ascii,
    "int": int,
    "float": float,
    "bytes": bytes,
    "datetime": Text.convert_to_datetime,
    "bool": lambda x: x in ["1", "True", "true"],
    "array": Json.load,
    "json": Json.load,
}

DTYPE2TYPE = {
    "int": int,
    "bool": bool,
    "float": float,
    "bytes": bytes,
    "str": str,
    "array": list,
    "json": dict,
    "datetime": datetime,
}

KEY_VALUE_PATTERN = r"^(.+)[=:](.+)$"


def convert_key_value(arg: str, subtype: str) -> tuple:
    matched = re.match(KEY_VALUE_PATTERN, arg)
    if not matched:
        return (None, arg)
    key, value = matched.groups()
    return (key, TEXT_CONVERTERS[subtype](value))


class DTypes:
    @staticmethod
    def to_sqlite_type(dtype: str):
        if dtype in SUPPORT_DTYPES:
            # if in extended dtypes, the type is upper of the dtype name
            return SQLITE_BUILTIN_DTYPES.get(dtype, dtype.upper())
        return "TEXT"

    @staticmethod
    def sqlite_converter(dtype: str):
        """Get type converter for a Python value that want to be saved into SQLite Database"""
        if dtype in SQLITE_BUILTIN_DTYPES:
            return DTYPE2TYPE[dtype]
        return get_sqlite_converter(dtype)

    @staticmethod
    def python_converter(dtype: str):
        """Get type converter for a value read from SQLite Database"""
        if dtype in SQLITE_BUILTIN_DTYPES:
            return DTYPE2TYPE[dtype]
        return get_python_converter(dtype)

    @staticmethod
    def text_converter(dtype: str, context_dtype: str = None):
        if context_dtype == "json" and dtype != "json":
            return lambda value: convert_key_value(value, dtype)
        return TEXT_CONVERTERS.get(dtype, None)

    def cast_to_sqlite(value, dtype: str, default=None):
        if dtype not in SUPPORT_DTYPES:
            return default
        if isinstance(value, DTYPE2TYPE[dtype]):
            return DTypes.sqlite_converter(dtype)(value)
        return default

    def cast_with_converters(value, converters, default=None):
        if not converters:
            return value
        if not isinstance(converters, (tuple, list)):
            converters = [converters]

        for converter in converters:
            if isinstance(converter, type):
                if isinstance(value, converter):
                    return value
            if not callable(converter):
                continue
            try:
                return converter(value)
            except:
                continue
        return default

    def cast_heterogeneous_with_converters(obj: dict, **key_converters) -> dict:
        result = {}
        for key, converters in key_converters.items():
            if key not in obj:
                continue
            casted_value = DTypes.cast_with_converters(obj[key], converters)
            if casted_value is not None:
                result[key] = casted_value
        return result

    def cast(value, dtype: str, default=None):
        if dtype not in SUPPORT_DTYPES:
            return value
        if isinstance(value, DTYPE2TYPE[dtype]):
            return value
        if isinstance(value, str):
            try:
                return TEXT_CONVERTERS[dtype](value)
            except:
                pass
        return default

    def cast_heterogeneous(obj: dict, **key_dtypes):
        result = {}
        for key, dtype in key_dtypes.items():
            if key not in obj:
                continue
            casted_value = DTypes.cast(obj[key], dtype)
            if casted_value is not None:
                result[key] = casted_value
        return result
