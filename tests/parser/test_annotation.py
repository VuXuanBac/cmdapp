from tests.helper import *
from cmdapp.parser.annotation import AnnotationParser


@with_cases(
    handler=AnnotationParser.parse,
    inputs={
        "all": "[item_id] w, hello (*array[int]: [1, 2, 3] = [1, 2, 3]): set width scale to the column",
        "no_datatype": "hello with:comment",
        "no_comment": '  *  (datetime: ["hello"])',
        "comment_only": " : comment jers : (helo, world)",
        "datatype_only": "(array = [1, 2, 3])",
        "flags_only": "hello, world",
        "metavar_only": "[\thello_world ]",
        "metavar_with_dtype": "[hello12](*int: [1, 3])",
        "special": "p (int = 1): page index (based 1)",
        "multiline": """hello(\t*array[int]: ["hello", "helo=world", "hello:3"] = [1, 2, 3] ): set width scale to the column,
             in display order""",
    },
    expects={
        "all": dict(
            flags=["w", "hello"],
            metavar="item_id",
            comment="set width scale to the column",
            dtype="array",
            proc="int",
            required=True,
            choices=[1, 2, 3],
            default=[1, 2, 3],
        ),
        "no_comment": dict(flags=[], dtype="datetime", choices=["hello"]),
        "comment_only": dict(comment="comment jers : (helo, world)"),
        "datatype_only": dict(dtype="array", default=[1, 2, 3]),
        "flags_only": dict(flags=["hello", "world"]),
        "metavar_only": dict(metavar="hello_world"),
        "metavar_with_dtype": dict(
            metavar="hello12", dtype="int", choices=[1, 3], required=True
        ),
        "no_datatype": dict(flags=["hello with"], comment="comment"),
        "special": dict(
            flags=["p"], dtype="int", default=1, comment="page index (based 1)"
        ),
        "multiline": dict(
            flags=["hello"],
            dtype="array",
            proc="int",
            required=True,
            choices=["hello", "helo=world", "hello:3"],
            default=[1, 2, 3],
            comment="set width scale to the column,\n             in display order",
        ),
    },
)
def test_parse_annotation(output, expect, case):
    assert same_data(output, expect)
