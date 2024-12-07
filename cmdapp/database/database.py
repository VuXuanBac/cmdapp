from ..parser import TableMeta

from .connection import DbConnection
from .table import Table


class Database:
    def __init__(
        self,
        database_path: str,
        schema: dict[str, TableMeta],
        *,
        aliases: dict[str, str] = {},
        row_factory_name: str = "dict",
    ):
        self.conn = DbConnection(database_path, row_factory=row_factory_name)
        tables_list = [
            Table(self.conn, name, table_meta) for name, table_meta in schema.items()
        ]
        self.tables = {table.name: table for table in tables_list}
        sanitized_aliases = {
            key: value for key, value in aliases.items() if value in self.tables
        }
        self.aliases = {
            table.human_name(1): table.name for table in tables_list
        } | sanitized_aliases

    def __getattr__(self, name):
        return getattr(self.conn, name)

    def __getitem__(self, name):
        table_name = self.aliases.get(name, name)
        return self.tables[table_name]

    def __contains__(self, key):
        return key in self.tables or key in self.aliases

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
