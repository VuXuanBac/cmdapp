from tests.helper import *
from datetime import datetime
from cmdapp.parser import COLUMN_ID, FieldMeta

FIELD_DATA = {
    "c1": dict(name="greet", metadata="g, hi(*str[telex] = hello world) : greeting"),
    "c2": dict(
        name="123 -@#12",
        metadata=dict(
            dtype="invalid",
            another=123,
            required=123,
            choices={},
            nargs=":",
            flags="hi",
            action="invalid",
            default=False,
        ),
    ),
    "c3": dict(
        name="h",
        metadata=dict(
            choices={"1": 12, "2": 34},
            flags=["hello"],
            annotation="*(*datetime = 241215): comment",
        ),
    ),
    "c4": dict(name=COLUMN_ID, metadata={}),
}


@with_cases(
    FieldMeta,
    inputs=FIELD_DATA,
    expects={
        "c1": dict(
            name="greet",
            metadata=dict(
                flags=["g", "hi"],
                required=True,
                dtype="str",
                proc="telex",
                default_value="hello world",
                comment="greeting",
            ),
        ),
        "c2": dict(
            name="123 -@#12",
            metadata=dict(
                dtype="str",
                required=True,
                flags=["h", "i"],
                default_value="False",
            ),
        ),
        "c3": dict(
            name="h",
            metadata=dict(
                dtype="datetime",
                flags=["hello"],
                comment="comment",
                required=True,
                default_value=datetime(2024, 12, 15),
                choices=["1", "2"],
            ),
        ),
        "c4": dict(name=COLUMN_ID, metadata=dict(dtype="str")),
    },
)
def test_field_meta_init(output: FieldMeta, expect, case):
    assert has_attributes(output, expect)
