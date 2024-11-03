from tests.helper import *

from cmdapp.database import (
    SQLCondition,
    SQLOperators,
)

####### SQL Condition #######


@with_cases(
    SQLCondition.convert_to_string,
    inputs={
        "G1": {
            "condition": ("age", SQLOperators.BETWEEN, (15, 65)),
            "negative": False,
        },
        "G2": {
            "condition": ("name", SQLOperators.LIKE, r"%abc%"),
            "negative": True,
        },
        "R1": {
            "condition": ("name", SQLOperators.BETWEEN, 123, 456),
            "negative": False,
        },
        "R2": {
            "condition": ("name", SQLOperators.IN, 123),
            "negative": True,
        },
        "R3": {
            "condition": None,
            "negative": True,
        },
    },
    expects={
        "G1": r"age BETWEEN 15 AND 65",
        "G2": r"NOT name LIKE '%abc%'",
        "R1": ("ValueError", "syntax for SQL condition is invalid"),
        "R2": ("ValueError", "syntax for SQL condition is invalid"),
        "R3": ("ValueError", "syntax for SQL condition is invalid"),
    },
)
def test_convert_to_string(output, expect, case):
    if case[0] == "R":
        assert output[0] == expect[0]
        assert contains_all(output[1][0], [expect[1]])
    else:
        assert same_data(output, expect)


def test_combine():
    condition = (
        SQLCondition("age", SQLOperators.GREATER_THAN, 15, negative=True)
        .AND("subject", SQLOperators.IN, ["maths", "physics"])
        .OR("score", SQLOperators.BETWEEN, (4, 7), negative=True)
    )
    assert same_data(
        condition.build(),
        "NOT age > 15 AND subject IN ('maths', 'physics') OR NOT score BETWEEN 4 AND 7",
    )
