import sqlite3
from .cursor import RowFactory

# Cursor is like a ITERATOR that can traversal over the result records


class DbConnection:
    def __init__(self, database_path, *, row_factory: str = "dict"):
        self.conn = sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = getattr(
            RowFactory, f"{row_factory}_factory", sqlite3.Row
        )

    def close(self):
        return self.conn.close()

    def with_transaction(self, handler, on_error=None):
        result = None
        try:
            self.conn.execute("BEGIN TRANSACTION")
            result: sqlite3.Cursor = handler(self.conn)
            self.conn.commit()
        except sqlite3.Error as error:
            self.conn.rollback()
            result = None
            if on_error:
                on_error(error)
        return result

    def execute(self, sql: str, data=None, on_error=None):
        with self.conn:
            try:
                return self.conn.execute(sql, data or {})
            except sqlite3.Error as error:
                if callable(on_error):
                    on_error(error, sql=sql, data=data)
        return None

    def batch_execute(
        self, sql: str, data: list[dict], batch_size: int = 10, on_error=None
    ):
        with self.conn:
            for batch in range(0, len(data), batch_size):
                batch_data = data[batch : batch + batch_size]
                _handler = lambda conn: conn.executemany(sql, batch_data)
                _on_error = (
                    (lambda error: on_error(error, sql=sql, data=batch_data))
                    if callable(on_error)
                    else None
                )
                cursor = self.with_transaction(handler=_handler, on_error=_on_error)
                yield cursor
