from cmdapp.base import *
from cmdapp.core import start_app
from cmdapp.database import Database
from cmdapp.parser.table import TableMeta
from cmdapp.render import Template, ResponseFormatter

DATABASE_SCHEMA = [
    TableMeta(
        name="person",
        plural="people",
        columns={
            "name": "n (*str[telex]): name of the record",
            "team_id": "t, team (*int): id of the team that the record belongs to",
            "gender": 'g (str: ["male", "female", "other"]): gender',
            "dob": {
                "annotation": "(datetime): date of birth",
                "metavar": "birthday",
            },
        },
        meta_columns=["created_at", "updated_at", "deleted_at"],
        constraints=["UNIQUE(name, team_id)"],
    ),
    TableMeta(
        name="team",
        singular="group",
        columns={"name": "n (*str[telex]): name of the record"},
        meta_columns=["created_at", "updated_at", "deleted_at"],
        constraints=["UNIQUE(name)"],
    ),
]

TEMPLATES = {
    "action": Template(
        "+[{style}]@[ on {action}][ {what}][ within {scope}][ with {argument}][ = {value}][ because {reason}][: |result][{result}]"
    ),
    "argument": Template(
        "[ The argument][ \[{argument}\]][ is {status}][ because {reason}][. {result}][. {recommend}]"
    ),
    "found": Template(
        "[NOT |negative][FOUND][ {count}][/{total}][ {what}][ with {field}][: {items}]"
    ),
    "exception": Template(
        "/*R[ERROR][ \[{type}\]][: |message]*Y['{message}']/*R[ on executing:\n|command]@C[{command}]@R[\n with |argument]@Y[{argument}]"
    ),
}


def prepare_sample_database():
    database = Database(":memory:", DATABASE_SCHEMA)
    good = database.prepare()
    if not good:
        errors = database.get_errors()
        print(
            ["Failed to initialize the database. Check the SQLite syntax!\n"]
            + [
                f"[{error['table']}] ERROR [{error['type']}] '{error['message']}' on executing\n{error['sql']}"
                for error in errors
            ]
        )
        return None
    return database


if __name__ == "__main__":
    database = prepare_sample_database()
    start_app(
        app_name="User Manager",
        app_class=BaseApp,
        app_prototypes=BasePrototype(database),
        database=database,
        response_formatter=ResponseFormatter(TEMPLATES),
    )
