from cmdapp.base import *
from cmdapp.core import start_app
from cmdapp.database import Database

DATABASE_SCHEMA = {
    "person": {
        "plural": "people",
        "columns": {
            "name": "n (*str[telex]): name of the record",
            "team_id": "t, team (*int): id of the team that the record belongs to",
            "gender": 'g (str: ["male", "female", "other"]): gender',
            "dob": {
                "annotation": "(datetime): date of birth",
                "metavar": "birthday",
            },
        },
        "meta-columns": ["created_at", "updated_at", "deleted_at"],
        "constraints": ["UNIQUE(name, team_id)"],
    },
    "team": {
        "singular": "group",
        "columns": {"name": "n (*str[telex]): name of the record"},
        "meta-columns": ["created_at", "updated_at", "deleted_at"],
        "constraints": ["UNIQUE(name)"],
    },
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
        app_prototypes=BasePrototype({"table": database.tables}),
        database=database,
    )
