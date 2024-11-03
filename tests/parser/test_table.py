from tests.helper import *
from cmdapp.parser.table import *

TABLE_METADATA = {
    "c1": {
        "columns": {
            "name": "(*str): username",
            "dob": "(datetime): date of birth",
            "gender": "(bool = 0): male (true) or female (false)",
        },
        "meta-columns": ["created_at", "deleted_at"],
        "constraints": ["UNIQUE(name, dob)"],
    },
    "c2": {
        "columns": {
            "123 invalid name": ": username",
        },
    },
}

TABLE_META_INSTANCE = TableMeta("user", TABLE_METADATA["c1"])


@with_cases(
    TableMeta,
    inputs={
        "c1": dict(name="user", metadata=TABLE_METADATA["c1"]),
        "c2": dict(name="123 hello world", metadata=TABLE_METADATA["c2"]),
    },
    expects={
        "c1": dict(
            name="user",
            columns_in_order=[
                COLUMN_ID,
                "name",
                "dob",
                "gender",
                COLUMN_CREATE,
                COLUMN_DELETE,
            ],
            constraints=["UNIQUE(name, dob)"],
        ),
        "c2": dict(
            name="_23_hello_world",
            columns_in_order=[
                COLUMN_ID,
                "_23_invalid_name",
            ],
        ),
    },
)
def test_table_meta_init(output: TableMeta, expect, case):
    columns = TABLE_METADATA[case]["columns"]
    meta_column_names = [COLUMN_ID] + TABLE_METADATA[case].get("meta-columns", [])
    meta_columns = {k: FieldMeta(k, META_COLUMNS[k]) for k in meta_column_names}
    extended_expect = expect | dict(
        columns={
            FieldHelper.sanitize_name(k): FieldMeta(k, v) for k, v in columns.items()
        }
        | meta_columns,
        meta_column_names=meta_column_names,
    )
    if "columns_in_order" in extended_expect:
        assert list(output.columns) == extended_expect.pop("columns_in_order")
    assert has_attributes(output, extended_expect)


@with_cases(
    TABLE_META_INSTANCE.filter_columns,
    inputs={
        "c1": "meta",
        "c2": ["name", "meta"],
        "c3": ["^name", "^gender"],
        "c4": ["meta", "^id"],
        "c5": [
            "name",
            "^dob",
            "gender",
            "^meta",
            "deleted_at",
            "updated_at",
        ],
    },
    expects={
        "c1": ["id", "created_at", "deleted_at"],
        "c2": ["id", "name", "created_at", "deleted_at"],
        "c3": ["id", "dob", "created_at", "deleted_at"],
        "c4": list(TABLE_META_INSTANCE.columns),
        "c5": ["name", "gender", "deleted_at"],
    },
    pass_directly=True,
)
def test_filter_columns(output, expect, case):
    assert same_data(output, expect)
