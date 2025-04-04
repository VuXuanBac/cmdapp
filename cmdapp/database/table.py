import sqlite3

from .connection import DbConnection
from .helper import CursorHelper, parse_error
from .sql import SQLBuilder
from .condition import SQLCondition
from .constants import *
from ..utils import Sanitizer

from ..parser import (
    TableMeta,
    COLUMN_ID,
    COLUMN_DELETE,
)


class Table:
    def __init__(self, connection: DbConnection, table_meta: TableMeta) -> None:
        self.conn = connection
        self.table_meta = table_meta
        self.name = Sanitizer.as_identifier(table_meta.name)
        self.errors = []

    def execute(self, sql: str, data=None):
        return self.conn.execute(sql, data=data, on_error=self.on_error)

    def batch_execute(self, sql: str, data: list[dict], batch_size: int = 10):
        return self.conn.batch_execute(
            sql, data=data, batch_size=batch_size, on_error=self.on_error
        )

    def on_error(self, error: sqlite3.Error | Exception, sql=None, data=None):
        error_name, message = parse_error(error)
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

    def __contains__(self, name):
        return name in self.table_meta

    def prepare(self):
        self.refresh()
        sql = SQLBuilder.create_table(self.name, self.table_meta)
        cursor = self.execute(sql)
        return CursorHelper.as_status(cursor, on_rowcount=False)

    # ######### DML #########

    def insert(self, item: dict):
        self.refresh()
        values = self.table_meta.sanitize_data(item)
        meta_values = self.table_meta.action_callback("create")

        sql, data = SQLBuilder.insert(self.name, values | meta_values)
        cursor = self.execute(sql, data)
        return CursorHelper.as_id(cursor)

    def update(self, item: dict, condition: SQLCondition = None):
        self.refresh()
        none_values = {k: v for k, v in item.items() if v is None}
        values = self.table_meta.sanitize_data(item)
        meta_values = self.table_meta.action_callback("update")

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

        meta_values = self.table_meta.action_callback("delete")
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
            new_id = self.insert(item)
            count += int(new_id is None)
            errors.extend(self.errors)
        self.errors = errors
        return count

    def insert_batch(self, items: list[dict], batch_size: int = 10):
        self.refresh()
        values = self.table_meta.sanitize_data(*items)
        meta_values = self.table_meta.action_callback("create")

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

    def get_columns(self, columns: list[str], item_ids: list[int] = None):
        if not columns:
            return {}
        self.refresh()
        sql = SQLBuilder.select(
            self.name,
            columns=columns + [COLUMN_ID],
            condition=(
                SQLCondition(COLUMN_ID, SQLOperators.IN, item_ids) if item_ids else None
            ),
        )
        cursor = self.execute(sql)

        records = CursorHelper.as_objects(cursor)
        return {
            record.pop(COLUMN_ID): (record[columns[0]] if len(columns) == 1 else record)
            for record in records
        }

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

    def translate(self, column_name: str, *values, full_record: bool = False) -> dict:
        """From values on a column, get the ID of matched records. This method is best to call with a UNIQUE column

        Args:
            column_name (str): Name of column to matched values
            full_record (bool): True if want to return full record instead of just record's ID. Default: False
            values: Values to match

        Returns:
            dict: Map each column value to matched data (record or ID)
        """
        if not values:
            return {}
        self.refresh()
        condition = SQLCondition(column_name, SQLOperators.IN, values)
        sql = SQLBuilder.select(
            self.name,
            columns=None if full_record else [COLUMN_ID, column_name],
            condition=condition,
        )
        cursor = self.execute(sql)
        match_records = CursorHelper.as_objects(cursor)
        if not match_records:
            return {}
        dictionary = {}
        for record in match_records:
            dictionary.setdefault(record[column_name], []).append(
                record if full_record else record[COLUMN_ID]
            )
        return dictionary
