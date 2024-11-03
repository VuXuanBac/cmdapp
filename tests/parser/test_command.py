from tests.helper import *
from cmdapp.parser.command import *

COMMAND_METADATA = {
    "c1": dict(
        description="Create new record",
        arguments={"permanent": "p (bool = 0): set to delete permanently"},
        dependencies={
            "arguments": "hello",
            "parser": lambda x, context: f"[Create] {context}: {x}",
        },
    ),
    "c2": dict(
        description="Update an existing record",
        epilog="Using `--no-<column_name>` to set column to null",
        custom=True,
        dependencies={
            "type": "table",
            "values": ["table_a", "table_b"],
            "arguments": lambda table: {
                f"{table}_arg_{i:03}": f"a{i} (int = {i}): number argument {i}"
                for i in range(5, 7)
            },
        },
    ),
    "c3": dict(
        arguments={
            "format": "f (int: [0, 1, 2] = 1): table style",
            "widths": "w (array[int]): set width scale to the column",
        },
        category="Print",
    ),
    "c4": dict(),
}


# @with_cases(
#     CommandMeta,
#     inputs=COMMAND_METADATA,
#     expects={
#         "c1": dict(
#             description="Create new record",
#             arguments=COMMAND_METADATA["c1"]["arguments"],
#             context_type=None,
#             # value_parser=COMMAND_METADATA["c1"]["dependencies"]["parser"],
#         ),
#         "c2": dict(
#             description="Update an existing record",
#             epilog="Using `--no-<column_name>` to set column to null",
#             with_argparser_options=dict(with_unknown_args=True),
#             context_type="table",
#             context_values=["table_a", "table_b"],
#             # arguments_for=COMMAND_METADATA["c2"]["dependencies"]["arguments"],
#             value_parser=None,
#         ),
#         "c3": dict(
#             arguments=COMMAND_METADATA["c3"]["arguments"],
#             context_type=None,
#             category="Print",
#         ),
#         "c4": dict(description="", epilog="", arguments={}, context_type=None),
#     },
# )
# def test_command_meta_init(output: CommandMeta, expect: dict, case):
#     assert has_attributes(output, expect)


COMMAND_META_INSTANCE = CommandMeta(
    description="Update an existing record",
    epilog="Using `--no-<column_name>` to set column to null",
    arguments={
        "permanent": "p (bool = 0): set to delete permanently",
        "AAA arg 005": ": this argument conficts with context AAA",
    },
    dependencies={
        "type": "table",
        "values": ["table_a", "table_b"],
        "arguments": lambda context: {
            f"{context} arg {i:03}": f"a{i} (int = {i}): number argument {i}"
            for i in range(5, 7)
        },
        "parser": lambda x, context: f"[VERSION 1.0] {context}: {x}",
    },
)


@with_cases(
    COMMAND_META_INSTANCE._get_argparser_attributes,
    inputs={"c1": None, "c2": "AAA"},
    expects={
        "c1": dict(
            description="Update an existing record",
            epilog="Using `--no-<column_name>` to set column to null",
            arguments={
                "permanent": FieldHelper.parse(
                    "p (bool = 0): set to delete permanently"
                ),
                "AAA arg 005": FieldHelper.parse(
                    ": this argument conficts with context AAA"
                ),
            },
        ),
        "c2": dict(
            description="[VERSION 1.0] AAA: Update an existing record",
            epilog="[VERSION 1.0] AAA: Using `--no-<column_name>` to set column to null",
            arguments={
                "permanent": FieldHelper.parse(
                    "p (bool = 0): [VERSION 1.0] AAA: set to delete permanently"
                ),
                "AAA arg 005": FieldHelper.parse(
                    ": [VERSION 1.0] AAA: this argument conficts with context AAA"
                ),
            }
            | {
                f"AAA arg {i:03}": FieldHelper.parse(
                    f"a{i} (int = {i}): [VERSION 1.0] AAA: number argument {i}"
                )
                for i in range(6, 7)
            },
        ),
    },
    pass_directly=True,
)
def test_create_argparser(output: dict, expect, case):
    assert same_data(output, expect)
