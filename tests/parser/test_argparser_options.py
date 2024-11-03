from datetime import datetime
from tests.helper import *
from cmdapp.parser.field import *

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
    ArgParserOptions.argparser_flags,
    inputs={
        "c1": dict(name="hello", flags=None),
        "c2": dict(name="a", flags=[]),
        "c3": dict(name="greeting", flags=["h", "12-hi*"]),
        "c4": dict(name="_123_good_work", flags=["  hell no ", "", "*"]),
    },
    expects={
        "c1": ["--hello"],
        "c2": [],
        "c3": ["-h", "--12-hi", "--greeting"],
        "c4": ["--hell-no", "--123-good-work"],
    },
)
def test_argparser_flags(output, expect, case):
    assert same_data(output, expect)


@with_cases(
    ArgParserOptions.from_metadata,
    inputs={
        "bool": dict(
            name="activate",
            metadata=dict(
                dtype="bool",
                required=True,
                default_value=0,
                comment="set true to activate",
            ),
        ),
        "array": dict(
            name="work",
            metadata=dict(dtype="array", required=True, nargs=5, flags=["w"]),
        ),
        "positional": dict(
            name="release",
            metadata=dict(
                dtype="datetime",
                flags=[],
                required=False,
                proc="telex",  # not used
                choices=["20241212", "20211222"],
                default_value="20241212",
                comment="release date",
            ),
        ),
    },
    expects={
        "bool": dict(
            flags=["--activate"],
            help="[bool] [=: 0] set true to activate",
            action="store_true",
            dest="activate",
        ),
        "array": dict(
            flags=["-w", "--work"],
            required=True,
            help="[array] [not null]",
            type=str,
            default=None,
            nargs=5,
            dest="work",
        ),
        "positional": dict(
            flags=[],
            nargs="?",
            choices=["20241212", "20211222"],
            default="20241212",
            type=DTypes.text_converter("datetime"),
            help="[datetime] [=: 20241212] release date",
            dest="release",
        ),
    },
)
def test_argparser_options(output, expect, case):
    assert output == expect
