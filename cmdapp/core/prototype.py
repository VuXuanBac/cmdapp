from typing import Callable

from ..parser import CommandMeta

from .command import CommandBuilder

# command `do_` function attribute to store CommandMeta
COMMAND_ATTRIBUTE_FOR_PROTOTYPE = "command_meta"


def create_commands(
    name: str,
    prototype: Callable,
    context_stores: dict[str, object],
) -> dict[str, Callable]:
    """Create commands from prototype and context stores. This will create 2 types of command:
    - If the prototype depends on contexts:
      - For each context, one command was parsed and created with this context
        - The command name is in format: `do_{command_name}_{context_name}`
        - The command function is the prototype function that is feeded with one keyword argument with name is the context type and value is the context.
        - So inside the prototype function, we can use the context object
      - One placeholder command for introducing the context-specific commands above
        - Placeholder command has only one argument that is the context type of its all subcommands
    - If the prototype NOT depends on any context:
      - One normal command

    Args:
        name (str): Command name
        prototype (Callable): Prototype function, that a function has an CommandMeta attribute
        context_stores (dict[str, object]): Stores of contexts to parse the CommandMeta. Key is the context type and value is context container. Each context container also an dict that map from context name and the context itself

    Returns:
        dict[str, Callable]: Created commands (include context-specific commands) and their corresponded names
    """
    command_meta: CommandMeta = getattr(
        prototype, COMMAND_ATTRIBUTE_FOR_PROTOTYPE, None
    )

    if not command_meta:
        return {f"do_{name}": prototype}, None
    # Remove because it is not used anymore
    delattr(prototype, COMMAND_ATTRIBUTE_FOR_PROTOTYPE)

    options = command_meta.with_argparser_options
    category = command_meta.category
    context_type = command_meta.context_type
    contexts = command_meta.get_contexts(context_stores)

    created_commands = {}
    for context_value, context in contexts.items():
        argparser = command_meta.create_argparser(context)
        command = CommandBuilder.create_command(
            f"{name}_{context_value}",
            prototype,
            argparser,
            options,
            **{context_type: context},
        )
        if command:
            created_commands[command.__name__] = command
    # if has any context subcommands
    if contexts:
        command = CommandBuilder.create_placeholder_command(
            name,
            list(contexts),
            context_type,
            default_derived_command=None,
            description=command_meta.description,
            epilog=command_meta.epilog,
        )
    # else: it is a normal command
    else:
        argparser = command_meta.create_argparser()
        command = CommandBuilder.create_command(name, prototype, argparser, options)

    if command:
        created_commands[command.__name__] = command
    return created_commands, category


class Prototype:
    """This class used to defined command logic prototype for the application.
    - A prototype function is a function with name prefixed with `do_` and it has a `CommandMeta` attribute, this `CommandMeta` will be used to parsed the command arguments
    - You can use `@as_command` decorator to any functions inside this class.
    - Prototype function treated as staticmethod of the Prototype class and should receive following arguments:
      - app: The CmdApp object that the created command should belongs to
      - args: A `ArgParser.Namespace` object that hold the parsed user-input-arguments
      - custom_args: A dict that hold the unknown arguments of the command. Should declared if the `CommandMeta` object has: `custom = True`
      - kwargs: Keywords arguments that represent the context the `CommandMeta` depends on. Should declared if the `CommandMeta` object has: `dependencies`
    - One prototype function not always corresponding to one application command.
    - Each context object declared on `CommandMeta` will issue one subcommand from the prototype function. And all these subcommands will be hidden. They will be introduced by a placeholder command.
    """

    def __init__(self, context_stores: dict[str, object] = None, category: str = None):
        """
        Args:
            context_stores (dict[str, object]): Contexts to parse `CommandMeta`
            category (str = None): Category for all commands created from this Prototype containers
        """
        self.context_stores = context_stores
        class_name = self.__class__.__name__
        self.category = category or (
            f"{class_name[:-len(Prototype.__name__)]} Commands"
            if class_name.endswith(Prototype.__name__)
            else f"{class_name} Commands"
        )

    def apply_to(self, app_class) -> dict:
        """Apply all prototypes defined in this class as commands on an app

        Args:
            app_class (Class object): App class to receive commands created from prototypes

        Returns:
            All main commands (not include context-specific commands) in their categories (if prototype has no category, it belongs to None category)
        """

        command_categories = {}
        cls = self.__class__
        attributes = dir(cls)
        prototypes = {
            key[3:]: getattr(cls, key) for key in attributes if key.startswith("do_")
        }
        for command_name, prototype in prototypes.items():
            if not callable(prototype):
                continue
            commands, category = create_commands(
                command_name, prototype, self.context_stores
            )
            for method_name, method in commands.items():
                if hasattr(app_class, method_name):
                    raise ValueError(
                        f"the attribute [{method_name}] has been used on [{app_class}]",
                        "try another name for the command",
                    )
                setattr(app_class, method_name, method)
            category = category or self.category
            if category in command_categories:
                command_categories[category].append(command_name)
            else:
                command_categories[category] = [command_name]
        return command_categories
