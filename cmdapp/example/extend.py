import random
from datetime import timedelta, datetime

from cmdapp.core import as_command, Prototype
from cmdapp.utils import Hash
from cmdapp.render import Response

from .context import *


# Defines more commands for the app
class ExtendedPrototype(Prototype):
    @as_command(
        description="Seed more data",
        arguments={
            "count": "c (*int): number of records",
            "scale": "s (int = 50): scale for random",
            "table": '* (str: ["person", "team"] = person): name of table',
        },
    )
    def do_seed(app: BaseApp, args):
        total, random_scale, table_name = Hash.get(
            vars(args), count=0, scale=5, table=None
        )
        table = app.database[table_name]
        if not table:
            return app.perror(
                Response.message(
                    TEMPLATES["found_info"],
                    negative=True,
                    what=f"table named {table_name}",
                )
            )
        data = []
        for i in range(total):
            item = (
                {
                    "name": f"Name #{random.randint(1, random_scale):03}",
                    "team_id": random.randint(1, random_scale),
                    "dob": datetime.today()
                    + timedelta(weeks=random.randint(-4000, -1000)),
                    "gender": random.choice(["male", "female", "other"]),
                }
                if table.name == "person"
                else {"name": f"Name #{random.randint(1, random_scale):03}"}
            )
            data.append(item)

        success = table.insert_batch(data)
        message_kwargs = dict(
            action="SEED",
            what=table.name,
            result=f"{success}/{len(data)} {table.display_name(success)} were created",
        )
        if success > 0:
            app.poutput(Response.message(TEMPLATES["success"], **message_kwargs))
        else:
            app.perror(Response.message(TEMPLATES["error"], **message_kwargs))
        app.print_database_errors()


if __name__ == "__main__":
    database = prepare_sample_database()
    start_app(
        app_name="User Manager",
        app_class=BaseApp,
        # Apply commands from BasePrototype and ExtendedPrototype
        app_prototypes=[BasePrototype({"table": database.tables}), ExtendedPrototype()],
        database=database,
    )
