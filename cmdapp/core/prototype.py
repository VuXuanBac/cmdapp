from typing import Callable

from ..parser import CommandMeta

from .command import CommandBuilder
from .context import ContextStore

# command `do_` function attribute to store CommandMeta
COMMAND_ATTRIBUTE_FOR_PROTOTYPE = "command_meta"


class Prototype:
    """This class used to defined command logic prototype for the application.
    - A prototype function is a function with name prefixed with `do_` and it has a `CommandMeta` attribute, this `CommandMeta` will be used to parsed the command arguments
    - You can use `@as_command` decorator to any functions inside this class.
    - Prototype function treated as staticmethod of the Prototype class and should receive following arguments:
      - app: The CmdApp object that the created command should belongs to
      - args: A `ArgParser.Namespace` object that hold the parsed user-input-arguments
      - custom_args: A list that hold the unknown arguments of the command. Should declared if the `CommandMeta` object has: `custom = True`
      - kwargs: Keywords arguments that represent the context the `CommandMeta` depends on. Should declared if the `CommandMeta` object has: `dependencies`
    - One prototype function not always corresponding to one application command.
    - Each context object declared on `CommandMeta` will issue one subcommand from the prototype function. And all these subcommands will be hidden. They will be introduced by a placeholder command.
    """

    def __init__(self, context_store: ContextStore = None, category: str = None):
        """
        Args:
            context_stores (dict[str, object]): Object to store contexts and their data to parse `CommandMeta`
            category (str = None): Category for all commands created from this Prototype containers
        """
        self.context_store = context_store
        class_name = self.__class__.__name__
        self.category = category or (
            f"{class_name[:-len(Prototype.__name__)]} Commands"
            if class_name.endswith(Prototype.__name__)
            else f"{class_name} Commands"
        )

    def contexted_arguments_creator(
        self, context: str, command: str = None
    ) -> dict | None:
        pass

    def contexted_value_parser(
        self, context: str, value: str, command: str = None
    ) -> str:
        pass

    def _create_contexted_commands(
        self, command_name: str, prototype: Callable, command_meta: CommandMeta
    ) -> dict:
        created_commands = {}
        context_type = self.context_store.type
        contexts = self.context_store.get_contexts(command_meta.dependencies)
        if not contexts:
            return None

        contexted_arguments_creator = lambda context: self.contexted_arguments_creator(
            context, command_name
        )
        contexted_value_parser = lambda context, value: self.contexted_value_parser(
            context, value, command_name
        )
        for context, context_data in contexts.items():
            argparser = command_meta.create_contexted_argparser(
                context,
                contexted_arguments_creator=contexted_arguments_creator,
                contexted_value_parser=contexted_value_parser,
            )
            command = CommandBuilder.create_command(
                f"{command_name}_{context}",
                prototype,
                argparser,
                command_meta.with_argparser_options,
                **{context_type: context_data},
            )
            if command:
                created_commands[command.__name__] = command

        command = CommandBuilder.create_placeholder_command(
            command_name,
            list(contexts),
            context_type,
            default_derived_command=None,
            description=command_meta.description,
            epilog=command_meta.epilog,
        )
        if command:
            created_commands[command.__name__] = command
        return created_commands

    def create_commands(
        self, command_name: str, prototype: Callable
    ) -> tuple[dict[str, Callable], str]:
        """Create commands from prototype and context stores. This will create 2 types of commands:
        - If the prototype depends on contexts:
            - For each context, one command was parsed and created with this context
                - The command name is in format: `do_{command_name}_{context}`
                - The command function is the prototype function that is fed with one keyword argument with name is the context type and value is the context data.
                - So inside the prototype function, we can use the context data
            - One placeholder command for introducing the context-specific commands created above
                - Placeholder command has single argument that is the context type of its all subcommands
        - If the prototype NOT depends on any context:
            - One normal command

        Args:
            command_name (str): Command name
            prototype (Callable): Prototype function, that a function has an CommandMeta attribute

        Returns:
            tuple:
            - dict[str, Callable]: Created commands (include context-specific commands) and their corresponded names
            - str: Category for created commands
        """
        command_meta: CommandMeta = getattr(
            prototype, COMMAND_ATTRIBUTE_FOR_PROTOTYPE, None
        )

        if not command_meta:
            return {f"do_{command_name}": prototype}, None
        # Remove because it is not used anymore
        delattr(prototype, COMMAND_ATTRIBUTE_FOR_PROTOTYPE)

        created_commands = {}
        # it should be parsed with contexts
        if command_meta.dependencies:
            created_commands = self._create_contexted_commands(
                command_name, prototype, command_meta
            )
        # it is a normal command or fail to created contexted commands
        if not created_commands:
            argparser = command_meta.create_argparser()
            command = CommandBuilder.create_command(
                command_name, prototype, argparser, command_meta.with_argparser_options
            )
            if command:
                created_commands[command.__name__] = command
        return created_commands, command_meta.category
