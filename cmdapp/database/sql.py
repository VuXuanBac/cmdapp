from .constants import *
from .condition import SQLCondition

from ..types import DTypes
from ..parser import TableMeta, FieldMeta, COLUMN_ID
from ..utils import Array, Hash, Sanitizer


class SQLBuilder:
    @staticmethod
    def create_column(field: FieldMeta) -> str:
        if field.name == COLUMN_ID:
            return f"{COLUMN_ID} INTEGER PRIMARY KEY"
        name = Sanitizer.as_identifier(field.name)
        dtype = field.metadata.get("dtype", "str")
        default_value, required = Hash.get(
            field.metadata, default_value=None, required=False
        )
        sqlite_type = DTypes.to_sqlite_type(dtype)
        default_part = (
            f" DEFAULT {DTypes.cast_to_sqlite(default_value, dtype)}"
            if default_value is not None
            else ""
        )
        return f"{name} {sqlite_type}{' NOT NULL' if required else ''}{default_part}"

    @staticmethod
    def create_table(name: str, table: TableMeta):
        constraints = [c.strip() for c in table.constraints if c and not c.isspace()]
        constraints = (",\n" if constraints else "") + ",\n".join(constraints)

        commands = ",\n".join(
            [SQLBuilder.create_column(field) for field in table.columns.values()]
        )
        return f"CREATE TABLE IF NOT EXISTS {name} (\n{commands}{constraints}\n)"

    @staticmethod
    def insert(table: str, data: dict | list[dict]):
        if not isinstance(data, (list, tuple)):
            data = [data]
        columns = [col for col in data[0] if col != COLUMN_ID]
        return (
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join([f':{col}' for col in columns])})",
            Array.unpack_one(data),
        )

    @staticmethod
    def update(table: str, data: dict, condition: SQLCondition = None):
        if condition is None:
            condition = SQLCondition.with_id()

        set_clause = ", ".join([f"{col} = :{col}" for col in data if col != COLUMN_ID])

        return (
            f"UPDATE {table} SET {set_clause} WHERE {condition.build()}",
            data,
        )

    @staticmethod
    def delete(table: str, condition: SQLCondition = None, data: dict = None):
        if condition is None:
            return f"TRUNCATE TABLE {table}", data
        where_clause = f" WHERE {condition.build()}"
        return f"DELETE FROM {table}{where_clause}", data

    @staticmethod
    def join(
        table: str,
        column: str,
        to_table: str,
        to_column: str = COLUMN_ID,
        alias=None,
        join_type: str = None,
    ):
        alias = alias or to_table
        join_type = (str(join_type) or "inner").upper()
        return f"{join_type} JOIN {to_table} AS {alias} ON {table}.{column} = {alias}.{to_column}"

    @staticmethod
    def select(
        table: str,
        columns: str | list[str] = None,
        condition: SQLCondition = None,
        joins: list[str] = None,
        group_by: list[str] = None,
        order_by: list[tuple[str, SQLOrderByDirection]] = None,
        limit: int = None,
        offset: int = None,
    ):
        columns = columns or "*"
        if isinstance(columns, (list, tuple)):
            columns = ", ".join(columns)

        orders = [f"{item[0]} {item[1]}" for item in order_by] if order_by else []

        join_clause = " " + " ".join(joins) if joins else ""
        where_clause = f" WHERE {condition.build()}" if condition else ""
        group_clause = f" GROUP BY {', '.join(group_by)}" if group_by else ""
        order_clause = f" ORDER BY {', '.join(orders)}" if orders else ""
        limit_clause = f" LIMIT {limit}" if isinstance(limit, int) else ""
        offset_clause = f" OFFSET {offset}" if isinstance(offset, int) else ""
        return f"SELECT {columns} FROM {table}{join_clause}{where_clause}{group_clause}{order_clause}{limit_clause}{offset_clause}"
