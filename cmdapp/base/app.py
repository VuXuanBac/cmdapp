from ..database import Database
from ..core import CmdApp
from ..render import Response
from .message import TEMPLATES


class BaseApp(CmdApp):
    def __init__(
        self,
        database: Database = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.database = database
        # self.add_setting("verbose", bool, False, "Show errors with detail")
        self.debug = True

    # def on_change_settings(self, param_name, old, new):
    #     if param_name == "verbose":
    #         if new == True:
    #             self.do_set("debug true")
    #             self.print_database_errors()

    def on_before_loop(self):
        print("_" * 80 + "\n")

    def on_after_loop(self):
        print("_" * 80 + "\n")

    def terminate(self, status_code=0):
        self.database.close()
        return super().terminate(status_code)

    def print_database_errors(self):
        errors = self.database.get_errors()
        if not self.debug or not errors:
            return
        self.perror(Response.message(TEMPLATES["custom"], "-" * 80))
        for error in errors:
            self.perror(
                Response.message(
                    TEMPLATES["exception"],
                    type=error["type"],
                    message=error["message"],
                    command=error["sql"],
                    argument=error["data"],
                )
            )
            self.perror(Response.message(TEMPLATES["custom"], "-" * 80))
