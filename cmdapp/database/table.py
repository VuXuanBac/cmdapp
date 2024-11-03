import sqlite3
from .connection import DbConnection
from .cursor import CursorHelper
from .sql import SQLBuilder
from .condition import SQLCondition
from .constants import *

from ..parser import (
    TableMeta,
    COLUMN_ID,
    COLUMN_DELETE,
)


class Table:
    def __init__(self, connection: DbConnection, table_meta: TableMeta) -> None:
        self.conn = connection
        self.table_meta = table_meta
        self.name = table_meta.name
        self.display_name = table_meta.name_with_number
        self.errors = []

    def execute(self, sql: str, data=None):
        return self.conn.execute(sql, data=data, on_error=self.on_error)

    def batch_execute(self, sql: str, data: list[dict], batch_size: int = 10):
        return self.conn.batch_execute(
            sql, data=data, batch_size=batch_size, on_error=self.on_error
        )

    def on_error(self, error: sqlite3.Error | Exception, sql=None, data=None):
        error_type = type(error).__name__
        message = str(error)
        if isinstance(error, sqlite3.Error):
            error_name = (
                error.sqlite_errorname
                if hasattr(error, "sqlite_errorname")
                else error_type
            )
        else:
            error_name = error_type

        self.errors.append(
            {
                "table": self.name,
                "type": error_name,
                "message": message,
                "sql": sql,
                "data": data,
            }
        )

    def refresh(self):
        self.errors = []

    def __getattr__(self, name):
        return getattr(self.table_meta, name)

    def prepare(self):
        self.refresh()
        sql = SQLBuilder.create_table(self.table_meta)
        cursor = self.execute(sql)
        return CursorHelper.as_status(cursor, on_rowcount=False)

    # ######### DML #########

    def insert(self, item: dict):
        self.refresh()
        values = self.table_meta.sanitize_data(item)
        meta_values = self.table_meta.meta_column_value("create")

        sql, data = SQLBuilder.insert(self.name, values | meta_values)
        cursor = self.execute(sql, data)
        return CursorHelper.as_rowcount(cursor)

    def update(self, item: dict, condition: SQLCondition = None):
        self.refresh()
        none_values = {k: v for k, v in item.items() if v is None}
        values = self.table_meta.sanitize_data(item)
        meta_values = self.table_meta.meta_column_value("update")

        sql, data = SQLBuilder.update(
            self.name, values | meta_values | none_values, condition
        )

        if none_values or len(values) > int(COLUMN_ID in values):
            cursor = self.execute(sql, data)
        else:
            self.on_error(
                ValueError(
                    "Missing attributes to update or all provided attributes are invalid"
                ),
                sql=sql,
                data=data,
            )
            cursor = None

        return CursorHelper.as_rowcount(cursor)

    def delete(self, condition: SQLCondition = None, permanent: bool = False):
        self.refresh()
        if condition is None:
            self.on_error(
                ValueError(
                    "require [condition] to filter out records should be deleted"
                )
            )
            return CursorHelper.as_rowcount(None)

        meta_values = self.table_meta.meta_column_value("delete")
        if permanent or not meta_values:
            sql, data = SQLBuilder.delete(self.name, condition)
        else:
            sql, data = SQLBuilder.update(self.name, meta_values, condition)

        cursor = self.execute(sql, data)

        return CursorHelper.as_rowcount(cursor)

    def insert_all(self, items: list[dict]):
        self.refresh()
        errors = []
        count = 0
        for item in items:
            count += self.insert(item)
            errors.extend(self.errors)
        self.errors = errors
        return count

    def insert_batch(self, items: list[dict], batch_size: int = 10):
        self.refresh()
        values = self.table_meta.sanitize_data(*items)
        meta_values = self.table_meta.meta_column_value("create")

        sql, data = SQLBuilder.insert(self.name, [v | meta_values for v in values])
        batched_results = self.batch_execute(sql, data, batch_size=batch_size)
        count = 0
        for cursor in batched_results:
            count += CursorHelper.as_rowcount(cursor)
        return count

    def delete_by_id(self, *item_id: int, permanent: bool = False):
        condition = SQLCondition(COLUMN_ID, SQLOperators.IN, list(item_id))
        return self.delete(condition, permanent=permanent)

    # ######### Query #########

    def get(self, item_id: int):
        self.refresh()
        sql = SQLBuilder.select(
            self.name,
            condition=SQLCondition.with_id(item_id),
        )
        cursor = self.execute(sql)
        return CursorHelper.as_object(cursor)

    def which_exists(self, *item_id: int, with_deleted=True):
        self.refresh()
        condition = SQLCondition(COLUMN_ID, SQLOperators.IN, list(item_id))
        if not with_deleted and COLUMN_DELETE in self.table_meta:
            condition = condition.AND(COLUMN_DELETE, SQLOperators.IS_NULL)

        sql = SQLBuilder.select(self.name, columns=COLUMN_ID, condition=condition)
        cursor = self.execute(sql)
        return CursorHelper.as_values(cursor)

    def query(
        self,
        columns: str | list[str] = None,
        condition: SQLCondition = None,
        order_by: list[tuple[str, SQLOrderByDirection]] = None,
        page_size: int = None,
        page_index: int = 1,
    ):
        self.refresh()
        columns = self.table_meta.filter_columns(columns)
        if page_size is not None and int(page_size) > 0:
            limit = page_size
            offset = page_size * (page_index - 1)
        else:
            limit = None
            offset = None

        sql = SQLBuilder.select(
            self.name,
            columns=columns,
            condition=condition,
            order_by=order_by,
            limit=limit,
            offset=offset,
        )
        cursor = self.execute(sql)

        return CursorHelper.as_objects(cursor)

    def first(self):
        self.refresh()
        sql = SQLBuilder.select(self.name, columns="*", limit=1)
        cursor = self.execute(sql)
        return CursorHelper.as_object(cursor)

    def last(self):
        self.refresh()
        sql = SQLBuilder.select(
            self.name,
            columns="*",
            order_by=[("ROWID", SQLOrderByDirection.DESC)],
            limit=1,
        )
        cursor = self.execute(sql)
        return CursorHelper.as_object(cursor)

    def count(self, condition: SQLCondition = None):
        self.refresh()
        sql = SQLBuilder.select(self.name, columns="COUNT(*)", condition=condition)
        cursor = self.execute(sql)
        return CursorHelper.as_value(cursor)
