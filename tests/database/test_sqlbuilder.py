from tests.helper import *

from cmdapp.database import *
from cmdapp.parser import *

TABLE_NAME = "test"


@with_cases(
    FieldMeta,
    inputs={
        "c1": dict(
            name="greet", metadata="g, hi(*str[telex] = hello world) : greeting"
        ),
        "c2": dict(name="123 -@#12", metadata="*(*datetime = 241215): comment"),
        "c3": dict(name=COLUMN_ID, metadata={}),
    },
    expects={
        "c1": "greet TEXT NOT NULL DEFAULT hello world",
        "c2": "_23____12 DATETIME NOT NULL DEFAULT 2024-12-15T00:00:00",
        "c3": f"{COLUMN_ID} INTEGER PRIMARY KEY",
    },
)
def test_create_column(output: FieldMeta, expect, case):
    assert SQLBuilder.create_column(output) == expect


@with_cases(
    TableMeta,
    inputs={
        "c1": {
            "name": "anything",
            "columns": {
                "username": {"required": True, "dtype": "array", "proc": "telex"},
                "type": '(str: ["normal", "vip", "admin", "staff", "client"] = normal)',
                "file": {},
            },
            "meta_columns": [COLUMN_DELETE],
            "constraints": ["UNIQUE(username, type)"],
        }
    },
    expects={
        "c1": f"CREATE TABLE IF NOT EXISTS test (\nid INTEGER PRIMARY KEY,\nusername ARRAY NOT NULL,\ntype TEXT DEFAULT normal,\nfile TEXT,\ndeleted_at DATETIME,\nUNIQUE(username, type)\n)"
    },
)
def test_create_table(output: TableMeta, expect, case):
    assert SQLBuilder.create_table(TABLE_NAME, output) == expect


@with_cases(
    lambda x: SQLBuilder.insert(TABLE_NAME, **x),
    inputs={
        "WithOne": {
            "data": {"name": "hello world", "age": 12, "male": False, COLUMN_ID: 12}
        },
        "WithMany": {
            "data": [
                {"name": "name 1", "age": 12, "male": False},
                {"name": "name 2", "age": 13, "male": True, "address": "somewhere"},
                {"name": "name 3", "age": 14},
            ]
        },
    },
    expects={
        "WithOne": (
            r"INSERT INTO test (name, age, male) VALUES (:name, :age, :male)",
            {"name": "hello world", "age": 12, "male": False, COLUMN_ID: 12},
        ),
        "WithMany": (
            r"INSERT INTO test (name, age, male) VALUES (:name, :age, :male)",
            [
                {"name": "name 1", "age": 12, "male": False},
                {"name": "name 2", "age": 13, "male": True, "address": "somewhere"},
                {"name": "name 3", "age": 14},
            ],
        ),
    },
)
def test_insert(output, expect, case):
    assert same_data(output, expect)


@with_cases(
    lambda x: SQLBuilder.update(TABLE_NAME, **x),
    inputs={
        "WithoutCondition": {
            "data": {
                "name": "hello world",
                "age": 12,
                "male": False,
                COLUMN_ID: 12,
            },
            "condition": None,
        },
        "WithCondition": {
            "data": {"name": "anonymous", "male": False},
            "condition": SQLCondition("male", SQLOperators.IS_NULL, None),
        },
    },
    expects={
        "WithoutCondition": (
            rf"UPDATE test SET name = :name, age = :age, male = :male WHERE {COLUMN_ID} = :{COLUMN_ID}",
            {"name": "hello world", "age": 12, "male": False, COLUMN_ID: 12},
        ),
        "WithCondition": (
            "UPDATE test SET name = :name, male = :male WHERE male IS NULL",
            {"name": "anonymous", "male": False},
        ),
    },
)
def test_update(output, expect, case):
    assert output == expect


@with_cases(
    lambda x: SQLBuilder.delete(TABLE_NAME, **x),
    inputs={
        "WithCondition": {
            "condition": SQLCondition("male", SQLOperators.IS_NULL, None),
            "data": None,
        },
        "WithoutCondition": {"condition": None, "data": None},
        "WithData": {
            "condition": SQLCondition("age", SQLOperators.EQUAL, ":age"),
            "data": {"age": 12},
        },
    },
    expects={
        "WithCondition": ("DELETE FROM test WHERE male IS NULL", None),
        "WithoutCondition": ("TRUNCATE TABLE test", None),
        "WithData": (
            "DELETE FROM test WHERE age = :age",
            {"age": 12},
        ),
    },
)
def test_delete(output, expect, case):
    assert output == expect


@with_cases(
    lambda x: SQLBuilder.select(TABLE_NAME, **x),
    inputs={
        "WithColumns": {"columns": ["name", "created_at"]},
        "WithCondition": {
            "condition": SQLCondition("age", SQLOperators.GREATER_THAN, 12)
        },
        "WithOrder": {
            "order_by": [
                ("name", SQLOrderByDirection.ASC),
                ("age", SQLOrderByDirection.DESC),
            ]
        },
        "WithLimitAndOffset": {
            "limit": 10,
            "offset": 20,
        },
        "WithoutAll": {},
        "WithAll": {
            "condition": SQLCondition("name", SQLOperators.LIKE, r"%user%").AND(
                "age", SQLOperators.IS_NOT_NULL, None
            ),
            "order_by": [("name", SQLOrderByDirection.ASC)],
            "limit": 10,
            "offset": 2,
        },
    },
    expects={
        "WithColumns": "SELECT name, created_at FROM test",
        "WithCondition": "SELECT * FROM test WHERE age > 12",
        "WithOrder": "SELECT * FROM test ORDER BY name ASC, age DESC",
        "WithLimitAndOffset": "SELECT * FROM test LIMIT 10 OFFSET 20",
        "WithoutAll": "SELECT * FROM test",
        "WithAll": r"SELECT * FROM test WHERE name LIKE '%user%' AND age IS NOT NULL ORDER BY name ASC LIMIT 10 OFFSET 2",
    },
)
def test_select(output, expect, case):
    assert output == expect
