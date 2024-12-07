from datetime import datetime

from ..types import DTypes
from ..utils import Hash, Array

from .constants import *
from .field import FieldMeta, FieldHelper


META_COLUMNS = {
    COLUMN_ID: dict(dtype="int"),
    COLUMN_CREATE: dict(dtype="datetime", required=True),
    COLUMN_UPDATE: dict(dtype="datetime"),
    COLUMN_DELETE: dict(dtype="datetime"),
}

META_COLUMN_WITH_ACTION = {
    "create": COLUMN_CREATE,
    "update": COLUMN_UPDATE,
    "delete": COLUMN_DELETE,
}


class TableHelper:
    @staticmethod
    def parse_columns(table_metadata: dict):
        _columns = table_metadata.get("columns", {})
        if not isinstance(_columns, dict):
            _columns = {}

        _meta_columns = table_metadata.get("meta-columns", [])
        if not isinstance(_meta_columns, (tuple, list)):
            _meta_columns = []
        # columns are in order
        columns = [FieldMeta(COLUMN_ID, META_COLUMNS[COLUMN_ID])]
        columns += [FieldMeta(k, v) for k, v in _columns.items()]
        columns += [
            FieldMeta(k, v) for k, v in META_COLUMNS.items() if k in _meta_columns
        ]
        return {field.name: field for field in columns}

    @staticmethod
    def parse_constraints(table_metadata: dict):
        constraints_description = table_metadata.get("constraints", [])
        # TODO
        return constraints_description


class TableMeta:
    def __init__(self, metadata: dict):
        self.singular = metadata.get("singular", "")
        self.plural = metadata.get("plural", "")

        self.constraints = TableHelper.parse_constraints(metadata)

        columns = TableHelper.parse_columns(metadata)
        self.columns = columns
        self.columns_dtypes = {
            col_name: field["dtype"] for col_name, field in columns.items()
        }
        self.meta_column_names = [c for c in META_COLUMNS if c in columns]

    def __contains__(self, key):
        return key in self.columns

    def __getitem__(self, key):
        return self.columns.get(key, None)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return str(
            dict(name=self.name, columns=self.columns, constraints=self.constraints)
        )

    def meta_column_value(self, action="create"):
        column_name = META_COLUMN_WITH_ACTION.get(action, None)
        if column_name not in self:
            return {}
        return {column_name: DTypes.cast_to_sqlite(datetime.now(), "datetime")}

    def sanitize_data(self, *data: dict, columns: list[str] = None):
        if columns:
            columns_dtypes = Hash.filter(self.columns_dtypes, *columns)
        else:
            columns_dtypes = self.columns_dtypes
        result = [
            DTypes.cast_heterogeneous(data_item, **columns_dtypes) for data_item in data
        ]
        return Array.unpack_one(result)

    def get_columns_by_name(self, column: str) -> list[str]:
        if column == ALL_LITERAL:
            return list(self.columns)
        elif column == META_COLUMN_LITERAL:
            return self.meta_column_names
        elif column in self:
            return [column]
        return []

    def filter_columns(self, columns: list[str] = None):
        if not columns:
            return []
        includes, excludes = [], []
        if isinstance(columns, str):
            columns = [columns]
        for col in columns:
            if col[0] in EXCLUDE_LITERAL:
                excludes.append(self.get_columns_by_name(col[1:]))
            else:
                includes.append(self.get_columns_by_name(col))
        result = set(self.columns)
        if not excludes:
            result = set().union(*includes) or result
        else:
            ignores = set().union(*excludes)
            if includes:
                ignores.difference_update(*includes)
            result.difference_update(ignores)
            # result = set().union(*includes) or set(self.columns)
            # if excludes:
            #     result.difference_update(*excludes)
        # return in columns order
        return [col for col in self.columns if col in result]
