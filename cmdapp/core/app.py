import sys
from cmd2 import Cmd, Settable
from cmd2.utils import categorize as categorize_command

from ..types import DTypes
from ..render import Template


class CmdApp(Cmd):
    def __init__(self, app_name: str = None, prompt: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if prompt:
            self.prompt = prompt
        elif app_name:
            self.prompt = Template("*C[{app_name} >> ]").format(app_name=app_name)

    def add_setting(self, name: str, dtype: str, default_value, description: str):
        if hasattr(self, name):
            raise ValueError(
                f"the attribute [{name}] has been used on [{self.__class__}]",
                "try another name for setting",
            )
        converter = DTypes.text_converter(dtype) if isinstance(dtype, str) else dtype
        setattr(self, name, converter(default_value))
        self.add_settable(
            Settable(
                name, converter, description, self, onchange_cb=self.on_change_settings
            )
        )

    def on_change_settings(self, param_name, old, new):
        pass

    def on_before_loop(self):
        pass

    def on_after_loop(self):
        pass

    def terminate(self, status_code=0):
        sys.exit(status_code)

    def set_command_status(self, *name: str, status="hide"):
        for comm in name:
            if status == "hide" and comm not in self.hidden_commands:
                self.hidden_commands.append(comm)
            elif status == "unhide" and comm in self.hidden_commands:
                self.hidden_commands.remove(comm)
            elif status == "disable":
                self.disable_command(comm, "This command was disable")
            elif status == "enable":
                self.enable_command(comm)

    def set_visible_commands(self, *name: str):
        hidden = []
        for attr_name in dir(self):
            attr_value = getattr(self, attr_name)
            if not attr_name.startswith("do_") or not callable(attr_value):
                continue
            command_name = attr_name[3:]
            if command_name not in name:
                hidden.append(command_name)
        self.hidden_commands = hidden

    @classmethod
    def set_command_category(cls, *name: str, category: str):
        commands = [getattr(cls, f"do_{comm}", None) for comm in name]
        commands = [command for command in commands if command]
        if commands:
            categorize_command(commands, category)
