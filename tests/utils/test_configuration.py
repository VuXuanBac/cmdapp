from tests.helper import *
from cmdapp.core import Configuration

FIXTURE_PATH = r"tests/fixture"


def create_configuration(lines: list[str], default: dict = None):
    with open(FIXTURE_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))
    return Configuration(FIXTURE_PATH, default)


DEFAULT_CONFIG = [
    "Color.Primary = #00fa04",
    "Language   = vi     ",
    "Theme.Header.Type6.Size = 12",
    "Color.secondary  = #0323f0",
]


@with_cases(
    handler=create_configuration,
    inputs={
        "General": {"lines": DEFAULT_CONFIG},
        "Edge": {
            "lines": DEFAULT_CONFIG + ["Color ="],
            "default": {"color": {"primary": "#012345"}, "LEVEL": "easy"},
        },
    },
    expects={
        "General": {
            "color": {"primary": "#00fa04", "secondary": "#0323f0"},
            "language": "vi",
            "theme": {"header_type6_size": "12"},
        },
        "Edge": {
            "color": "",
            "language": "vi",
            "theme": {"header_type6_size": "12"},
            "level": "easy",
        },
    },
)
def test_configuration_init(output: Configuration, expect: dict, case):
    print(output)
    assert same_data(output.data, expect)
