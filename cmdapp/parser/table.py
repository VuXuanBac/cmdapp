from datetime import datetime
from typing import Callable

from ..types import DTypes
from ..utils import Hash, Array

from .constants import *
from .field import FieldMeta


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
    def parse_columns(columns: dict, meta_columns: list[str]) -> dict[str, FieldMeta]:
        if not isinstance(columns, dict):
            columns = {}

        if not isinstance(meta_columns, (tuple, list)):
            meta_columns = []
        # columns are in order
        all_columns = [FieldMeta(COLUMN_ID, META_COLUMNS[COLUMN_ID])]
        all_columns += [FieldMeta(k, v) for k, v in columns.items()]
        all_columns += [
            FieldMeta(k, v) for k, v in META_COLUMNS.items() if k in meta_columns
        ]
        return {field.name: field for field in all_columns}

    @staticmethod
    def parse_constraints(constraints: list[str]):
        # TODO
        return constraints or []


class TableMeta:
    def __init__(
        self,
        name: str,
        columns: dict[str, str | dict],
        meta_columns: list[str] = None,
        constraints: list[str] = None,
        *,
        singular: str = None,
        plural: str = None,
        action_callback: Callable = None,
    ):
        """Create a Table Meta object that describe the Database Table

        Args:
            name (str): Name of the table, use to reference it inside Database
            columns (dict[str, str  |  dict]): Annotation or Dict syntax to describe the table's columns
            action_callback (Callable): A function to call when an action `create`, `update` or `delete` performed on the `Table`. The function receive the action name and the record data (dict), its can perform transformations on the data and expect to return new data for the records
            meta_columns (list[str], optional): _description_. Defaults to None.
            constraints (list[str], optional): _description_. Defaults to None.
            singular (str, optional): _description_. Defaults to None.
            plural (str, optional): _description_. Defaults to None.
        """
        # print(f"Create TableMeta with name = {name}, columns = {columns}")
        self.name = name
        singular_name = singular or self.name
        plural_name = plural or (singular_name + "s")
        self._human_name = (singular_name, plural_name)

        self.constraints = TableHelper.parse_constraints(constraints)

        parsed_columns = TableHelper.parse_columns(columns, meta_columns)
        self.columns = parsed_columns
        self.columns_dtypes = {
            col_name: field["dtype"] for col_name, field in parsed_columns.items()
        }

        self.meta_column_names = [c for c in META_COLUMNS if c in parsed_columns]
        self.action_callback = action_callback or self.default_callback

    def human_name(self, number=1):
        return self._human_name[int(int(number) != 1)]

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

    def default_callback(self, action: str, data: dict = {}):
        column_name = META_COLUMN_WITH_ACTION.get(action, None)
        if column_name not in self:
            return data
        return data | {column_name: DTypes.cast_to_sqlite(datetime.now(), "datetime")}

    def sanitize_data(self, *data: dict):
        if len(data) == 1:
            return DTypes.cast_heterogeneous(data[0], **self.columns_dtypes)
        return [
            DTypes.cast_heterogeneous(data_item, **self.columns_dtypes)
            for data_item in data
        ]

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

    def to_json(self):
        return dict(
            name=self.name,
            singular=self._human_name[0],
            plural=self._human_name[1],
            columns={k: v.metadata for k, v in self.columns.items()},
            meta_columns=self.meta_column_names,
            constraints=self.constraints,
        )
