from .app import CmdApp
from .prototype import Prototype
from .decorator import as_command

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

    commands_with_categories = [(builtin_command_category, builtin_command_names)]
    for app_prototype in app_prototypes:
        if not isinstance(app_prototype, Prototype):
            continue
        categories = app_prototype.apply_to(app_class)
        commands_with_categories.extend(list(categories.items()))
    app: CmdApp = app_class(*args, **kwargs)
    visible_commands = []
    for category, command_names in commands_with_categories:
        app_class.set_command_category(*command_names, category=category)
        visible_commands.extend(command_names)
    app.set_visible_commands(*visible_commands)
    app.on_before_loop()
    app.cmdloop()
    app.on_after_loop()
    app.terminate()
    return app
