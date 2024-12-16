from datetime import datetime

from tests.helper import *
from cmdapp.render import FileFormat

SAMPLE_DATA = [
    # Contains non-basic Python data type (datetime) + Non ASCII text
    {
        "id": "C1234",
        "name": "Vũ Xuân Bắc",
        "dob": datetime(2001, 10, 10),
        "single": True,
        "children": [],
    },
    # None Value
    {"id": "G5678", "name": "Anonymous", "dob": None, "single": None, "children": []},
    # Missing Key + Contains Array (serialized with comma inside)
    {
        "id": "S9101",
        "name": "First",
        "dob": datetime(1995, 5, 12),
        "children": ["Second", "Third"],
    },
    # Change key order
    {
        "dob": datetime(2012, 1, 1),
        "single": True,
        "id": "S1121",
        "name": "Sun|day",
        "children": [],
    },
]


@with_cases(
    handler=FileFormat.write_csv,
    inputs={
        "NoHeader": {"options": dict(headers=False)},
        "Rename": {
            "options": dict(
                rename={"dob": "date of birth", "unknown": "keep", "name": "id"},
                restval="MISSING KEY",
            )
        },
        "Others": {
            "options": dict(delimiter="|", quotechar="/", restval="MISSING KEY")
        },
    },
    expects={
        "NoHeader": [
            "C1234,Vũ Xuân Bắc,2001-10-10 00:00:00,True,[]",
            "G5678,Anonymous,,,[]",
            "S9101,First,1995-05-12 00:00:00,,\"['Second', 'Third']\"",
            "S1121,Sun|day,2012-01-01 00:00:00,True,[]",
        ],
        # Unknown keys => Keep with `None` value
        # Existed name ("name" => "id") => Keep both values and rename as normal
        "Rename": [
            "date of birth,keep,id,id,single,children",
            "2001-10-10 00:00:00,MISSING KEY,Vũ Xuân Bắc,C1234,True,[]",
            ",MISSING KEY,Anonymous,G5678,,[]",
            "1995-05-12 00:00:00,MISSING KEY,First,S9101,MISSING KEY,\"['Second', 'Third']\"",
            "2012-01-01 00:00:00,MISSING KEY,Sun|day,S1121,True,[]",
        ],
        "Others": [
            "id|name|dob|single|children",
            "C1234|Vũ Xuân Bắc|2001-10-10 00:00:00|True|[]",
            "G5678|Anonymous|||[]",
            "S9101|First|1995-05-12 00:00:00|MISSING KEY|['Second', 'Third']",
            "S1121|/Sun|day/|2012-01-01 00:00:00|True|[]",
        ],
    },
    data=SAMPLE_DATA,
)
def test_write_csv(output: str, expect: list[str], case: str):
    print(output)
    assert output.splitlines() == expect


@with_cases(
    handler=FileFormat.write_json,
    inputs={
        "EnsureAscii": {"options": dict(ensure_ascii=True)},
        "Rename": {
            "options": dict(
                rename={"dob": "date of birth", "unknown": "keep", "name": "id"},
            )
        },
        "Others": {"options": dict(sort_keys=True)},
    },
    expects={
        # Non ASCII are escaped
        "EnsureAscii": r'[{"id": "C1234", "name": "V\u0169 Xu\u00e2n B\u1eafc", "dob": "2001-10-10T00:00:00", "single": true, "children": []}, {"id": "G5678", "name": "Anonymous", "dob": null, "single": null, "children": []}, {"id": "S9101", "name": "First", "dob": "1995-05-12T00:00:00", "children": ["Second", "Third"]}, {"dob": "2012-01-01T00:00:00", "single": true, "id": "S1121", "name": "Sun|day", "children": []}]',
        # Unknown keys => Keep with `None` value
        # Existed name ("name" => "id") => Remove name in key (remove 'name') and keep name in value (keep 'id' value)
        "Rename": r'[{"date of birth": "2001-10-10T00:00:00", "keep": null, "id": "C1234", "single": true, "children": []}, {"date of birth": null, "keep": null, "id": "G5678", "single": null, "children": []}, {"date of birth": "1995-05-12T00:00:00", "keep": null, "id": "S9101", "children": ["Second", "Third"]}, {"date of birth": "2012-01-01T00:00:00", "keep": null, "id": "S1121", "single": true, "children": []}]',
        "Others": r'[{"children": [], "dob": "2001-10-10T00:00:00", "id": "C1234", "name": "Vũ Xuân Bắc", "single": true}, {"children": [], "dob": null, "id": "G5678", "name": "Anonymous", "single": null}, {"children": ["Second", "Third"], "dob": "1995-05-12T00:00:00", "id": "S9101", "name": "First"}, {"children": [], "dob": "2012-01-01T00:00:00", "id": "S1121", "name": "Sun|day", "single": true}]',
    },
    data=SAMPLE_DATA,
)
def test_write_json(output: str, expect: list[str], case: str):
    print(output)
    assert output == expect


# yaml is same as json
# html is too complicated but rename is same as csv
