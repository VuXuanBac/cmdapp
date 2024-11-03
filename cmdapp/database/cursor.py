from collections import namedtuple

import sqlite3

from ..utils import Array


class CursorHelper:
    @staticmethod
    def as_status(cursor: sqlite3.Cursor | None, on_rowcount=True):
        if on_rowcount:
            return cursor and cursor.rowcount > 0
        return bool(cursor)

    @staticmethod
    def as_rowcount(cursor: sqlite3.Cursor | None):
        return cursor.rowcount if cursor else 0

    @staticmethod
    def as_object(cursor: sqlite3.Cursor | None):
        return cursor.fetchone() if cursor else None

    @staticmethod
    def as_objects(cursor: sqlite3.Cursor | None):
        return cursor.fetchall() if cursor else []

    @staticmethod
    def as_value(cursor: sqlite3.Cursor | None):
        result = cursor.fetchone() if cursor else None
        return Array.unpack_one(result.values()) if result else result

    @staticmethod
    def as_values(cursor: sqlite3.Cursor | None):
        result = cursor.fetchall() if cursor else None
        return (
            [Array.unpack_one(item.values()) for item in result] if result else result
        )


class RowFactory:
    """Define how to combined cursor values and columns name"""

    def dict_factory(cursor: sqlite3.Cursor, row):
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}

    def namedtuple_factory(cursor: sqlite3.Cursor, row):
        fields = [column[0] for column in cursor.description]
        cls = namedtuple("Row", fields)
        return cls._make(row)
