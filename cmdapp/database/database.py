import sqlite3
from collections import namedtuple

from ..parser import TableMeta

from .connection import DbConnection
from .table import Table


class Database:
    def __init__(
        self,
        database_path: str,
        schema: dict[str, dict],
        *,
        row_factory_name: str = "dict",
    ):
        self.conn = DbConnection(database_path, row_factory=row_factory_name)
        tables = [
            Table(self, TableMeta(name, metadata)) for name, metadata in schema.items()
        ]
        self.tables = {table.name: table for table in tables}

    def __getattr__(self, name):
        return getattr(self.conn, name)

    def __getitem__(self, name):
        return self.tables[name]

    def __contains__(self, key):
        return key in self.tables

    def get_errors(self):
        errors = []
        for _, table in self.tables.items():
            errors.extend(table.errors)
        return errors

    def prepare(self):
        status = True
        for _, table in self.tables.items():
            status &= table.prepare()
        return status
