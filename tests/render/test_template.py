from tests.helper import *
from cmd2.ansi import Fg, Bg, style as ansi_style
from cmd2.utils import TextAlignment
from cmdapp.render.template import Template, TemplateParser
from cmdapp.utils import Json
from enum import Enum


def json_serializer(obj):
    if isinstance(obj, Enum):
        return obj.name
    if callable(obj):
        return obj.__qualname__

    return Json.serializer(obj)


@with_cases(
    TemplateParser.parse_pattern,
    inputs={
        "c01": r"Hello \[World\]",
        "c02": r"",
        "c03": r"  Hello \[World\]|suffix",
        "c04": r"|command",
        "c05": r"Hello |comm with text|suf",
        "c06": r"Hello {0} with {word}|1,greet",
        "c07": r"Hello \{com}|command",
        "c08": r"Hello world |required,good",
        "c09": r"Hello {placeholder with space}",
        "c10": r"{com}",
        "c11": r"{com\}",
        "c12": r"With {not1text} part|not,#good",
    },
    expects={
        "c01": ("Hello [World]", []),
        "c02": None,
        "c03": ("  Hello [World]", ["suffix"]),
        "c04": ("|command", []),
        "c05": ("Hello |comm with text", ["suf"]),
        "c06": ("Hello {0} with {word}", ["0", "word", "1", "greet"]),
        "c07": ("Hello {{com}}", ["command"]),
        "c08": ("Hello world ", ["required", "good"]),
        "c09": ("Hello {placeholder with space}", []),
        "c10": ("{com}", ["com"]),
        "c11": ("{{com}}", []),
        "c12": ("With {not1text} part|not,#good", ["not1text"]),
    },
    pass_directly=True,
)
def test_parse_pattern(output, expect, case):
    assert same_data(output, expect)


@with_cases(
    TemplateParser.parse_format,
    inputs={
        "c1": dict(format="=*/~cD+", base_format={}),
        "c2": dict(format="10>", base_format={}),
        # inherit
        "c3": dict(
            format="&_xB#",
            base_format=dict(dim=True, alignment=TextAlignment.LEFT, fg=Fg.GREEN),
        ),
        # reset
        "c4": dict(
            format="@",
            base_format=dict(dim=True, alignment=TextAlignment.LEFT, fg=Fg.GREEN),
        ),
        # invalid order ==> None
        "c5": dict(format="&bx^", base_format={}),
    },
    expects={
        "c1": dict(
            alignment="CENTER",
            bold=True,
            italic=True,
            strikethrough=True,
            fg="LIGHT_CYAN",
            bg="DARK_GRAY",
            transform="str.upper",
        ),
        "c2": dict(alignment="RIGHT", width=10),
        "c3": dict(
            bg="BLUE", alignment="LEFT", underline=True, dim=True, transform="str.title"
        ),
        "c4": dict(),
        "c5": None,
    },
)
def test_parse_format(output: dict, expect: dict, case):
    assert same_data(output, expect, serializer=json_serializer)


@with_cases(
    TemplateParser.parse,
    inputs={
        "c1": r"=*/~cD+[{type}][ when {action}]&c[ {what}][ within {scope}]@[ with {argument}][ = {value}][ because {reason}]&30>[: {result}]",
        "c2": "{0}",
        "c3": "ERROR][ \\[{type}\\]]_^Yx[: '{message}']@#[ on executing:\n|message][{command}]&10=[\n with {argument}]",
        "c4": "] Special case] =/!\t[]*r-[ with invalid format]12*+&[ and it] has not applied][[ []",
    },
    expects={
        "c1": (
            ["=*/~cD+", "&c", "@", "&30>"],
            {
                0: [],
                1: ["{type}", " when {action}"],
                2: [" {what}", " within {scope}"],
                3: [" with {argument}", " = {value}", " because {reason}"],
                4: [": {result}"],
            },
        ),
        "c2": ([], {0: ["{0}"]}),
        "c3": (
            ["_^Yx", "@#", "&10="],
            {
                0: ["ERROR", r" \[{type}\]"],
                1: [": '{message}'"],
                2: [" on executing:\n|message", "{command}"],
                3: ["\n with {argument}"],
            },
        ),
        "c4": (
            ["=/!", "*r-"],  # remove invalid
            {
                0: [" Special case"],
                1: [],
                2: [" with invalid format", " and it", " has not applied"],
            },
        ),
    },
)
def test_parse(output, expect, case):
    formats, patterns = expect

    base_format = {}
    exp_formats = [base_format]
    for fm in formats:
        format = TemplateParser.parse_format(fm, base_format)
        exp_formats.append(format)
        base_format = format
    exp_patterns = {}
    for ind, ptns in patterns.items():
        exp_patterns[ind] = [TemplateParser.parse_pattern(ptn) for ptn in ptns]
    assert same_data(output[0], exp_formats, serializer=json_serializer)
    assert same_data(output[1], exp_patterns, serializer=json_serializer)


@with_cases(
    Template.apply_format,
    inputs={
        "c1": [
            "hello world",
            dict(
                transform=str.upper,
                alignment=TextAlignment.LEFT,
                width=15,
                bold=True,
                fg=Fg.GREEN,
            ),
        ],
        "c2": ["hello world", dict(width=40, transform="str.upper", invalid=True)],
    },
    expects={
        "c1": ansi_style("{0:<15}".format("HELLO WORLD"), bold=True, fg=Fg.GREEN),
        "c2": "hello world",
    },
)
def test_apply_format(output: str, expect: str, case):
    assert output == expect


SAMPLE_TEMPLATE = Template(
    "{message\\} ]+[{0}:]@[ \\[{type}\\] ][: '{message}']_^Yx[ on executing: \n|message,1][{command}]&10=[\n with {argument}]"
)


@with_cases(
    SAMPLE_TEMPLATE.format,
    inputs={
        "c1": ["error", "world", dict(type="invalid", command="SELECT * FROM books")],
        "c2": ["success", "do", dict(message="create one book")],
        "c3": [],
    },
    expects={
        "c1": "{message} ERROR: [invalid] "
        + Template.apply_format(
            "SELECT * FROM books", underline=True, overline=True, fg=Fg.YELLOW
        ),
        "c2": "{message} SUCCESS:: 'create one book'"
        + Template.apply_format(
            " on executing: \n", underline=True, overline=True, fg=Fg.YELLOW
        ),
        "c3": "{message} ",
    },
)
def test_format(output: str, expect: str, case):
    assert output == expect
