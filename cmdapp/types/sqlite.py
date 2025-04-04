import sqlite3
import json
from datetime import datetime

from ..utils import Json, Hash

SQLITE_BUILTIN_DTYPES = {
    "str": "TEXT",
    "int": "INTEGER",
    "float": "REAL",
    "bytes": "BLOB",
}

_SQLITE_PYTHON_CONVERTER = {
    "datetime": {
        "adapter": [datetime],
        "as_sqlite": datetime.isoformat,
        "as_python": datetime.fromisoformat,
    },
    "array": {
        "adapter": [list, tuple, set],
        "as_sqlite": Json.dump,
        "as_python": Json.load,
    },
    "json": {
        "adapter": [dict],
        "as_sqlite": Json.dump,
        "as_python": Json.load,
    },
    "bool": {
        "adapter": [bool],
        "as_sqlite": int,
        "as_python": lambda x: (x == "1"),
    },
    # "path": {
    #     "adapter": [type(Path())],
    #     "as_sqlite": lambda x: os.path.abspath(str(x)),  # Path(x).resolve(),  #
    #     "as_python": lambda x: x,  # Path(os.path.abspath(x))
    # },
}


def get_sqlite_converter(dtype: str):
    return Hash.dig(_SQLITE_PYTHON_CONVERTER, dtype, "as_sqlite", default=None)


def get_python_converter(dtype: str):
    return Hash.dig(_SQLITE_PYTHON_CONVERTER, dtype, "as_python", default=None)


######## Create interface between SQLite and Python ########
def _create_to_sqlite_converter(dtype):
    description = _SQLITE_PYTHON_CONVERTER.get(dtype, {})
    type_adapters = tuple(description.get("adapter", []))
    sqlite_converter = description.get("as_sqlite", None)
    if type_adapters and sqlite_converter:

        def adapter(data):
            if isinstance(data, type_adapters):
                return sqlite_converter(data)
            raise TypeError(
                f"parse {data} (a {type(data)} object) fail",
                f"expected an {dtype} object",
            )

        return type_adapters, adapter
    return None, None


def _create_to_python_converter(dtype):
    python_converter = get_python_converter(dtype)
    if python_converter:

        def converter(data: bytes):
            return python_converter(data.decode())

        return converter
    return None


SQLITE_EXTENDED_DTYPES = list(_SQLITE_PYTHON_CONVERTER)

for dtype in SQLITE_EXTENDED_DTYPES:
    type_adapters, adapter = _create_to_sqlite_converter(dtype)
    converter = _create_to_python_converter(dtype)
    if adapter:
        for ptype in type_adapters:
            sqlite3.register_adapter(ptype, adapter)
    if converter:
        sqlite3.register_converter(dtype.upper(), converter)

SUPPORT_DTYPES = list(SQLITE_BUILTIN_DTYPES) + SQLITE_EXTENDED_DTYPES
