import sys
from typing import Callable
from cmd2 import Cmd, Settable
from cmd2.plugin import CommandFinalizationData, PostcommandData, PostparsingData
from cmd2.utils import categorize as categorize_command

from ..types import DTypes
from ..render import Template, ResponseFormatter

from .prototype import Prototype
from .hook import Hook


class CmdApp(Cmd):
    def __init__(
        self,
        app_name: str = None,
        prompt: str = None,
        response_formatter: ResponseFormatter = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.response_formatter = response_formatter or ResponseFormatter()
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

    def register_hooks(self, hook: Hook):
        validate_hooks = hook.__class__.get_validate_hooks()
        for validator in validate_hooks.values():

            def _post_parsing(data: PostparsingData):
                new_statement = validator(self, data.statement)
                if new_statement:
                    data.statement = self.statement_parser.parse(new_statement)
                else:
                    data.stop = True
                return data

            self.register_postparsing_hook(_post_parsing)

        render_hooks = hook.__class__.get_render_hooks()
        for renderer in render_hooks.values():

            def _post_cmd(data: PostcommandData):
                new_result = renderer(self, data.stop, data.statement)
                data.stop = new_result
                return data

            self.register_postcmd_hook(_post_cmd)

        finalize_hooks = hook.__class__.get_finalize_hooks()
        for finalize in finalize_hooks.values():

            def _finalize(data: CommandFinalizationData):
                finalize(self, data.stop, data.statement)
                return data

            self.register_cmdfinalization_hook(_finalize)

        prepare_hooks = hook.__class__.get_prepare_hooks()
        for prepare in prepare_hooks.values():
            _prepare = lambda: prepare(self)
            self.register_cmdfinalization_hook(_prepare)

    @classmethod
    def register_commands(
        cls,
        commands: dict[str, Callable],
        category: str = None,
        ignore_used_names: bool = False,
    ):
        created_command_names = []
        for command_name, method in commands.items():
            if hasattr(cls, command_name):
                if ignore_used_names:
                    continue
                raise ValueError(
                    f"the attribute [{command_name}] has been used on [{cls}]",
                    "try another name for the command",
                )
            setattr(cls, command_name, method)
            categorize_command(method, category)
            created_command_names.append(command_name)
        return created_command_names

    @classmethod
    def register_prototype(cls, app_prototype: Prototype):
        """Apply all prototypes defined in this class as commands on an app

        Args:
            prototype (Prototype): App class to receive commands created from prototypes

        Returns:
            list: Names of applied commands (exclude derived commands)
        """

        applied_commands = []
        attributes = dir(app_prototype.__class__)
        commands = {
            key[3:]: getattr(app_prototype.__class__, key)
            for key in attributes
            if key.startswith("do_")
        }
        for command_name, command_prototype in commands.items():
            if not callable(command_prototype):
                continue
            commands, category = app_prototype.create_commands(
                command_name, command_prototype
            )
            success_commands = cls.register_commands(
                commands, category=category or app_prototype.category
            )
            if success_commands:
                applied_commands.append(command_name)
        return applied_commands
