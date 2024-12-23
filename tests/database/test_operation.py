import random

from tests.helper import *

from cmdapp.database import *
from cmdapp.parser import *

TABLE_NAME = "book"
TABLE_SCHEMA = {
    "name": TABLE_NAME,
    "columns": {
        "title": {"dtype": "str", "required": True, "comment": "title of the book"},
        "authors": {
            "dtype": "array",
            "comment": "authors of the book. first author is main author",
        },
        "year": {"dtype": "int", "comment": "publish year"},
        "pdf": {"dtype": "str"},
        "done": {"dtype": "bool", "required": True, "default": False},
        "type": {
            "dtype": "str",
            "required": True,
            "choices": ["image", "text", "remake"],
        },
    },
    "meta_columns": [COLUMN_CREATE, COLUMN_UPDATE, COLUMN_DELETE],
    "constraints": ["UNIQUE(title, year)", "UNIQUE(pdf)"],
}


#### Helper method ####
def assert_result(errors, output, expect: dict, case=None):
    assert output == expect["output"]
    assert len(errors) == len(expect["errors"])
    print("Errors: ", errors)
    for ind, error in enumerate(errors):
        expected_error = expect["errors"][ind]
        assert error["table"] == expected_error.get("table", None)
        assert error["type"] == expected_error["type"]
        assert contains_all(error["message"], expected_error["message"])


def test_prepare():
    database_schema = [
        TableMeta(**TABLE_SCHEMA),
        TableMeta(
            name="bad",
            columns={"group": "(*str): group name of users. column name is invalid"},
        ),
    ]
    database = Database(":memory:", database_schema)
    output = database.prepare()
    expect = {
        "output": False,
        "errors": [dict(type="OperationalError", message=["group"], table="bad")],
    }
    assert_result(database.get_errors(), output, expect)


######## Prepare data for next tests ########
ITEMS = []
for i in range(10):
    ITEMS.append(
        {
            "title": f"Title {i}",
            "authors": [f"Author {i}"],
            "year": 1925 + i,
            "pdf": f"path/to/file-{i}.pdf",
            "done": bool(random.randint(0, 1)),
            "type": TABLE_SCHEMA["columns"]["type"]["choices"][i % 3],
        }
    )


def prepare_table(with_populate=True, with_delete=False):
    database = Database(":memory:", [TableMeta(**TABLE_SCHEMA)])
    table = database[TABLE_NAME]
    table.prepare()
    if with_populate or with_delete:
        table.insert_batch(ITEMS)
    if with_delete:
        table.delete(SQLCondition("year % 3", SQLOperators.EQUAL, 0))
    return table


@with_object(
    prepare_table,
    "insert",
    inputs={
        # good
        "Good": {"title": "Hello World 1", "type": "image"},
        # invalid dtype on `year`
        "GoodWithInvalidType": {
            "title": "Hello World 2",
            "year": "invalid year",
            "type": "remake",
        },
        # missing title
        "ErrorMissing": {"type": "image"},
        # unique constraints
        "ErrorUnique": {"title": "Title 1", "year": 1926, "type": "image"},
    },
    expects={
        # rowcount, errors
        "Good": dict(output=1, errors=[]),
        "GoodWithInvalidType": dict(output=1, errors=[]),
        "ErrorMissing": dict(
            output=0,
            errors=[
                {
                    "type": "IntegrityError",
                    "message": ["not null", "title"],
                }
            ],
        ),
        "ErrorUnique": dict(
            output=0,
            errors=[
                {
                    "type": "IntegrityError",
                    "message": ["unique", "title", "year"],
                }
            ],
        ),
    },
    pass_directly=True,
)
def test_insert(table: Table, output, expect, case):
    if case.startswith("Error"):
        expect["errors"] = [error | {"table": table.name} for error in expect["errors"]]
    assert_result(table.errors, int(output > 0), expect, case)
    if case == "Good":
        last_record = table.get(output)
        assert last_record["title"] == "Hello World 1"
        assert last_record["type"] == "image"
    if case == "GoodWithInvalidType":
        last_record = table.get(output)
        assert last_record["title"] == "Hello World 2"
        assert last_record["type"] == "remake"
        assert last_record["year"] == None


@with_object(
    prepare_table,
    "update",
    inputs={
        "Good": dict(item={"id": 3, "year": 1900, "authors": ["Change 1", "Change 2"]}),
        # set null to nullable column
        "GoodWithNone": dict(
            item={"pdf": None, "title": "Another title"},
            condition=SQLCondition("id", SQLOperators.EQUAL, 6),
        ),
        # missing condition and id
        "ErrorMissing": dict(item={"title": "Hello"}),
        # no attributes to update: year is invalid
        "ErrorInvalidDtype": dict(item={"id": 3, "year": "path/to/file-3.pdf"}),
        # required constraints
        "ErrorConstraintRequired": dict(item={"id": 3, "type": None}),
        # unique constraints
        "ErrorConstraintUnique": dict(item={"id": 3, "title": "Title 1", "year": 1926}),
        "Many": dict(
            item={"year": None},
            condition=SQLCondition("year", SQLOperators.GREATER_THAN, 1930),
        ),
    },
    expects={
        # rowcount, error
        "Good": dict(output=1, errors=[]),
        "GoodWithNone": dict(output=1, errors=[]),
        "ErrorMissing": dict(
            output=0,
            errors=[
                {
                    "type": "ProgrammingError",
                    "message": ["not supply", "value", "binding parameter", ":id"],
                }
            ],
        ),
        "ErrorInvalidDtype": dict(
            output=0,
            errors=[
                {
                    "type": "ValueError",
                    "message": ["missing attributes", "attributes are invalid"],
                }
            ],
        ),
        "ErrorConstraintRequired": dict(
            output=0,
            errors=[{"type": "IntegrityError", "message": ["not null", "type"]}],
        ),
        "ErrorConstraintUnique": dict(
            output=0,
            errors=[{"type": "IntegrityError", "message": ["unique", "title", "year"]}],
        ),
        "Many": dict(output=4, errors=[]),  # 1934 - 1930
    },
)
def test_update(table: Table, output, expect, case: str):
    if case.startswith("Error"):
        expect["errors"] = [error | {"table": table.name} for error in expect["errors"]]
    assert_result(table.errors, output, expect, case)
    if case == "Good":
        record = table.get(3)
        assert record["year"] == 1900
        assert record["authors"] == ["Change 1", "Change 2"]
    if case == "GoodWithNone":
        record = table.get(6)
        assert record["pdf"] == None
        assert record["title"] == "Another title"
    if case == "Many":
        result = table.query(
            condition=SQLCondition("year", SQLOperators.GREATER_THAN, 1930)
        )
        assert result == []


@with_object(
    prepare_table,
    "delete",
    inputs={
        "Good": dict(condition=SQLCondition.with_id(3), permanent=False),
        "GoodPermanent": dict(condition=SQLCondition.with_id(3), permanent=True),
        "Many": dict(condition=SQLCondition("year", SQLOperators.GREATER_THAN, 1930)),
        "NotExist": dict(
            condition=SQLCondition(COLUMN_ID, SQLOperators.GREATER_THAN, 123)
        ),
        "ErrorNoCondition": dict(condition=None),
        "ErrorInvalidCondition": dict(
            condition=SQLCondition("something", SQLOperators.EQUAL, 20)
        ),
    },
    expects={
        "Good": dict(output=1, errors=[]),
        "GoodPermanent": dict(output=1, errors=[]),
        "Many": dict(output=4, errors=[]),
        "NotExist": dict(output=0, errors=[]),
        "ErrorNoCondition": dict(
            output=0,
            errors=[
                {
                    "type": "ValueError",
                    "message": ["require", "condition"],
                }
            ],
        ),
        "ErrorInvalidCondition": dict(
            output=0,
            errors=[
                {"type": "OperationalError", "message": ["no", "column", "something"]}
            ],
        ),
    },
)
def test_delete(table: Table, output, expect, case):
    if case.startswith("Error"):
        expect["errors"] = [error | {"table": table.name} for error in expect["errors"]]
    assert_result(table.errors, output, expect, case)
    if case in ["GoodPermanent", "Good"]:
        record = table.get(3)
        if case == "GoodPermanent":
            assert record == None
        else:
            assert record[COLUMN_DELETE] != None
            assert record["title"] == ITEMS[2]["title"]


@with_object(
    prepare_table,
    "insert_batch",
    inputs={
        "Good": {
            "items": [
                {"title": "Test 1", "type": "image"},
                {"title": "Test 2", "type": "text", "pdf": "./path/image.png"},
                {"title": "Test 3", "type": "image", "year": 2015},
                {"title": "Test 4", "type": "text", "year": 2010},
                {"title": "Test 5", "type": "remake"},
            ],
            "batch_size": 2,
        },
        "Error": {
            "items": [
                {"title": "Test 1", "type": "image", "year": 2020},
                {"title": "Test 2", "year": 2009, "done": True},  # missing `type`
                {"title": "Test 3", "type": "image", "year": 2015},
                {"title": "Test 4", "type": "text"},  # missing `year`
                {"title": "Test 1", "type": "remake", "year": 2020},  # ok
            ],
            "batch_size": 2,
        },
    },
    expects={
        "Good": dict(output=5, errors=[]),
        "Error": dict(
            output=1,
            errors=[
                {"type": "ProgrammingError", "message": ["binding", "type"]},
                {"type": "ProgrammingError", "message": ["binding", "year"]},
            ],
        ),
    },
    with_populate=False,
)
def test_insert_batch(table: Table, output, expect, case):
    if case.startswith("Error"):
        expect["errors"] = [error | {"table": table.name} for error in expect["errors"]]
    assert_result(table.errors, output, expect, case)
    assert table.count() == expect["output"]


@with_cases(
    prepare_table(with_delete=True).which_exists,
    inputs={
        "WithoutDelete": [*list(range(0, 15, 2)), {"with_deleted": False}],
        "WithDelete": [*list(range(0, 15, 2)), {"with_deleted": True}],
    },
    expects={
        "WithoutDelete": [4, 6, 10],
        "WithDelete": [2, 4, 6, 8, 10],
    },
)
def test_which_exists(output, expect, case):
    assert output == expect


@with_cases(
    prepare_table().query,
    inputs={
        "WithColumns": {"columns": ["^year", "done", "^pdf", "^meta", "title"]},
        "WithCondition": {
            "condition": SQLCondition("year", SQLOperators.GREATER_THAN, 1930)
        },
        "WithOrder": {
            "order_by": [
                ("type", SQLOrderByDirection.ASC),
                ("title", SQLOrderByDirection.DESC),
            ]
        },
        "WithPageSize": {
            "page_size": 2,
            "page_index": 3,
        },
        "WithoutAll": {},
        "WithAll": {
            "condition": SQLCondition("type", SQLOperators.EQUAL, "text"),
            "order_by": [("title", SQLOrderByDirection.DESC)],
            "page_size": 1,
            "page_index": 2,
        },
    },
    expects={
        "WithColumns": [
            {name: x[name] for name in ["title", "done", "authors", "type"]}
            for x in ITEMS
        ],
        "WithCondition": [item for item in ITEMS if item["year"] > 1930],
        "WithOrder": sorted(
            sorted(ITEMS, key=lambda x: x["title"], reverse=True),
            key=lambda x: x["type"],
        ),
        "WithPageSize": ITEMS[4:6],
        "WithoutAll": ITEMS,
        "WithAll": sorted(
            [item for item in ITEMS if item["type"] == "text"],
            key=lambda x: x["title"],
            reverse=True,
        )[1:2],
    },
)
def test_query(output, expect, case):
    def get_saved_value(items):
        result = []
        for item in items:
            if "pdf" not in item:
                result.append(item)
            else:
                special = {"pdf": (item.get("pdf", None))}
                result.append(item | special)
        return result

    output_without_meta_fields = [
        {k: v for k, v in x.items() if not (k.endswith("_at") or k == COLUMN_ID)}
        for x in output
    ]
    assert output_without_meta_fields == get_saved_value(expect)


@with_cases(
    prepare_table().translate,
    inputs={
        "SingleMatch": ["year", 1924, 1929, 1934, 1939],
        "MultiMatch": ["type", "image", "remake"],
        "NoMatch": ["year"] + list(range(1920, 1925)),
        "NoValues": ["year"],
        "FullRecord": ["year", 1924, 1929, 1934, 1939, dict(full_record=True)],
    },
    expects={
        "SingleMatch": {1929: [5], 1934: [10]},
        "MultiMatch": {"image": [1, 4, 7, 10], "remake": [3, 6, 9]},
        "NoMatch": {},
        "NoValues": {},
        "FullRecord": {1929: [5], 1934: [10]},
    },
)
def test_translate(output, expect, case):
    if case == "FullRecord":
        for key, records in output.items():
            for index, record in enumerate(records):
                assert COLUMN_CREATE in record
                assert COLUMN_UPDATE in record
                assert COLUMN_DELETE in record
                assert record[COLUMN_ID] == expect[key][index]
                data_record = {
                    k: v
                    for k, v in record.items()
                    if k not in [COLUMN_CREATE, COLUMN_UPDATE, COLUMN_DELETE, COLUMN_ID]
                }
                assert same_data(data_record, ITEMS[expect[key][index] - 1])
    else:
        assert same_data(output, expect)


@with_cases(
    prepare_table().get_columns,
    inputs={
        "SingleColumn": dict(columns=["year"], item_ids=[3, 5, 8, 13]),
        "MultipleColumns": dict(columns=["type", "year"], item_ids=[3, 5, 13]),
        "WithoutIds": dict(columns=["year"]),
    },
    expects={
        "SingleColumn": {3: 1927, 5: 1929, 8: 1932},
        "MultipleColumns": {
            3: dict(type="remake", year=1927),
            5: dict(type="text", year=1929),
        },
        "WithoutIds": {(i + 1): (1925 + i) for i in range(len(ITEMS))},
    },
)
def test_get_columns(output, expect, case):
    assert same_data(output, expect)
