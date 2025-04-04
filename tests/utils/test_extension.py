from tests.helper import *
from cmdapp.utils import Hash, Array


@with_cases(
    handler=Hash.filter,
    inputs={
        "FilterOnly": ["key", "missing"],
        "RenameOnly": dict(rename={"another key": "special key", "not found": "me"}),
        "Combine": [
            "key",
            "missing",
            dict(rename={"another key": "special key", "not found": "me"}),
        ],
        "ConflictName": [
            "key",
            "another key",
            dict(rename={"another key": "key", 123: "another key"}),
        ],
        "NotFound": ["anonymous", "dangerous", dict(rename={"special": "ignore"})],
    },
    expects={
        "FilterOnly": {"key": "value"},
        "RenameOnly": {"special key": True},
        "Combine": {"key": "value", "special key": True},
        "ConflictName": {"key": True, "another key": "number"},
        "NotFound": {},
    },
    d={"key": "value", 123: "number", "another key": True},
)
def test_hash_filter(output: dict, expect: dict, case):
    print(output)
    assert output == expect


@with_cases(
    handler=Hash.ignore,
    inputs={
        "FilterOnly": ["key", "missing"],
        "RenameOnly": dict(rename={"another key": "special key", "not found": "me"}),
        "Combine": [
            "key",
            "missing",
            dict(rename={"another key": "special key", "not found": "me"}),
        ],
        "ConflictName": [
            "key",
            "another key",
            dict(rename={"another key": "key", 123: "another key"}),
        ],
        "NotFound": ["anonymous", "dangerous", dict(rename={"special": "ignore"})],
    },
    expects={
        "FilterOnly": {123: "number", "another key": True},
        "RenameOnly": {"key": "value", 123: "number", "special key": True},
        "Combine": {123: "number", "special key": True},
        "ConflictName": {"another key": "number"},
        "NotFound": {"key": "value", 123: "number", "another key": True},
    },
    d={"key": "value", 123: "number", "another key": True},
)
def test_hash_ignore(output: dict, expect: dict, case):
    print(output)
    assert output == expect


@with_cases(
    handler=Hash.get_as_dict,
    inputs={
        "FilterOnly": ["key", "missing"],
        "DefaultValueOnly": {"another_key": "value changed", "not_found": "me"},
        "Combine": [
            "key",
            "missing",
            {"another_key": "special key", "not_found": "me"},
        ],
        "ConflictName": ["missing", "another_key", {"another_key": "value changed"}],
        "NotFound": ["anonymous", "dangerous", {"special": "keep"}],
    },
    expects={
        "FilterOnly": {"key": "value", "missing": None},
        "DefaultValueOnly": {"another_key": True, "not_found": "me"},
        "Combine": {
            "key": "value",
            "missing": None,
            "another_key": True,
            "not_found": "me",
        },
        "ConflictName": {"missing": None, "another_key": True},
        "NotFound": {"anonymous": None, "dangerous": None, "special": "keep"},
    },
    d={"key": "value", 123: "number", "another_key": True},
)
def test_hash_get_dict(output: dict, expect: dict, case):
    assert same_data(output, expect)


@with_cases(
    handler=Hash.dig,
    inputs={
        "Found": ["key1", "key2"],
        "NotFoundMiddle": ["key1", "key4", "key7"],
        "EndOfDataInMiddle": ["key1", "key2", "key3", "key4", "key5"],
    },
    expects={
        "Found": {"key3": "value3"},
        "NotFoundMiddle": None,
        "EndOfDataInMiddle": None,
    },
    d={"key1": {"key2": {"key3": "value3"}, "key4": {"key5": {"key6": "value6"}}}},
)
def test_hash(output: dict, expect: dict, case):
    assert same_data(output, expect)
