from ..database import Database
from ..core import CmdApp


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

    def terminate(self, status_code=0):
        self.database.close()
        return super().terminate(status_code)
