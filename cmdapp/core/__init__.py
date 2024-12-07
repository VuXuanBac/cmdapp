from .app import CmdApp
from .prototype import Prototype
from .decorator import as_command
from .configuration import Configuration
from .context import ContextStore
from .response import Response

DEFAULT_BUILTIN_COMMANDS = [
    "help",
    "set",
    "quit",
    "shell",
    "edit",
    "py",
    "history",
    "edit",
    "alias",
    "shortcuts",
]


def start_app(
    app_prototypes: Prototype | list[Prototype],
    app_class=CmdApp,
    builtin_command_names: list[str] = DEFAULT_BUILTIN_COMMANDS,
    builtin_command_category: str = "Builtin Commands",
    *args,
    **kwargs,
) -> CmdApp:
    """Initialize and Start an CmdApp

    Args:
        app_prototypes (Prototype): Objects that defines the commands logic for the app.
        app_class (CmdApp, optional): Class object of the app, this class should be inherited from `CmdApp`. Defaults to CmdApp.
        builtin_command_names (list[str], optional): Names of builtin commands that the app inherit from cmd2.Cmd
        builtin_command_category (str = "Builtin Commands"): Category for the builtin commands
        args, kwargs: Arguments used for creating CmdApp instance

    Returns:
        CmdApp: App instance
    """
    assert issubclass(app_class, CmdApp)
    if not isinstance(app_prototypes, list):
        app_prototypes = [app_prototypes]

    app_class.set_command_category(
        *builtin_command_names, category=builtin_command_category
    )
    created_command_names = []
    for app_prototype in app_prototypes:
        if not isinstance(app_prototype, Prototype):
            continue
        created_command_names.extend(app_class.register_prototype(app_prototype))
    app: CmdApp = app_class(*args, **kwargs)
    app.set_visible_commands(*(created_command_names + builtin_command_names))
    app.cmdloop()
    app.terminate()
    return app
