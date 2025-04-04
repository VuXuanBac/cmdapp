from ..parser import TableMeta

from .connection import DbConnection
from .table import Table
from .helper import CursorHelper


class Database:
    def __init__(
        self,
        database_path: str,
        schema: list[TableMeta],
        *,
        row_factory_name: str = "dict",
    ):
        self.conn = DbConnection(database_path, row_factory=row_factory_name)
        self.tables = {
            table_meta.name: Table(self.conn, table_meta) for table_meta in schema
        }
        self.aliases = {
            table.human_name(1): name for name, table in self.tables.items()
        }

    def __getattr__(self, name):
        return getattr(self.conn, name)

    def __getitem__(self, name):
        table_name = self.aliases.get(name, name)
        return self.tables[table_name]

    def __contains__(self, key):
        return key in self.tables or key in self.aliases

    def with_transaction(self, handler, on_error=None):
        return self.conn.with_transaction(handler, on_error)

    def query(self, sql: str, data: dict = None):
        cursor = self.conn.execute(sql, data)
        return CursorHelper.as_objects(cursor)

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
