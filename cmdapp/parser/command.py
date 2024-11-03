from cmd2 import Cmd2ArgumentParser
from .field import FieldMeta, FieldHelper


class CommandHelper:
    def parse_arguments_on_context(
        value_parser, context, description: str, epilog: str, arguments: dict
    ):
        """Use context object to parse text value [Side effect on `arguments`]

        Args:
            value_parser (Callable): Function to parse the text value
            context (Any): The context object
            description (str): Command description
            epilog (str): Command epilog
            arguments (dict): Command arguments. Each `comment` text will be parsed

        Returns:
            dict: Populated values for description, epilog and arguments
        """
        description = value_parser(description, context)
        epilog = value_parser(epilog, context)
        for name, metadata in arguments.items():
            if "comment" in metadata:
                metadata["comment"] = value_parser(metadata["comment"], context)
        return dict(description=description, epilog=epilog, arguments=arguments)

    def create_argparser_with_attributes(
        arguments: dict = {}, description="", epilog="", **kwargs
    ) -> Cmd2ArgumentParser:
        """Create `Cmd2ArgumentParser` for the command

        Args:
            arguments (dict[str, str | dict]): Arguments description
            description (str, optional): Command description. Defaults to "".
            epilog (str, optional): Command epilog. Defaults to "".

        Returns:
            Cmd2ArgumentParser:
        """
        argparser = Cmd2ArgumentParser(description=description, epilog=epilog, **kwargs)
        for name, meta in arguments.items():
            options = FieldMeta(name, meta).as_argparser_argument()
            flags = options.pop("flags", [])
            argparser.add_argument(*flags, **options)
        return argparser


class CommandMeta:
    def __init__(
        self,
        description: str = None,
        epilog: str = None,
        arguments: dict = None,
        dependencies: dict = None,
        category: str = None,
        custom: bool = False,
    ) -> None:
        """CommandMeta store data to create application commands

        Args:
            description (str): Description text describe the command
            epilog (str): Text describe the command, display like a post script
            arguments (dict): Arguments of the command with key is the argument name and value is a str or dict that used to created a `FieldMeta`
            dependencies (dict, optional): Specify all the contexts of the command. For each context, a subcommand will be created. The context can be used to parse custom arguments (for each subcommands) and parse text value (description, epilog, help...) corresponded to the context. Defaults to None.
            category (str, optional): Category for the command. Defaults to None.
            custom (bool, optional): True if the command accepts unknown arguments. Defaults to False.
        """
        self.description = description or ""
        self.epilog = epilog or ""
        self.arguments = arguments if isinstance(arguments, dict) else {}
        self.category = category or None
        self.with_argparser_options = dict(with_unknown_args=bool(custom))
        dependencies = dependencies or {}
        _arguments_for = dependencies.get("arguments", None)
        _value_parser = dependencies.get("parser", None)
        self.context_type = dependencies.get("type", None)
        self.context_values = dependencies.get("values", None)
        self.arguments_for = _arguments_for if callable(_arguments_for) else None
        self.value_parser = _value_parser if callable(_value_parser) else None

    def get_contexts(self, contexts_store: dict[str, object]) -> dict:
        """With contexts store, get all the contexts and their names that the command depends on

        Args:
            contexts_store (dict[str, object]): Key is the context type and value is context container. Each context container also an dict that map from context name and the context itself

        Returns:
            dict: The name and value of the context that the command depends on
        """
        context_containers: dict = (contexts_store or {}).get(self.context_type, None)
        if not context_containers or not isinstance(context_containers, dict):
            return {}
        context_values = self.context_values or list(context_containers)
        return {k: v for k, v in context_containers.items() if k in context_values}

    def _get_argparser_attributes(self, context=None) -> dict:
        """Helper method for `create_argparser`"""
        if not context:
            return {
                "description": self.description,
                "epilog": self.epilog,
                "arguments": {
                    name: FieldHelper.parse(metadata)
                    for name, metadata in self.arguments.items()
                },  # avoid side effect
            }
        arguments = self.arguments
        if self.arguments_for:
            extended_arguments = self.arguments_for(context)
            if not isinstance(extended_arguments, dict):
                raise ValueError(
                    f"get arguments for context {context} fail because the returned value {extended_arguments} is not a dict"
                )
            # when context arguments confict name with normal arguments: normal argument has higher priority
            arguments = extended_arguments | arguments
        attributes = {
            "description": self.description,
            "epilog": self.epilog,
            "arguments": {
                name: FieldHelper.parse(metadata)
                for name, metadata in arguments.items()
            },
        }
        if self.value_parser:
            attributes = CommandHelper.parse_arguments_on_context(
                self.value_parser, context, **attributes
            )
        return attributes

    def create_argparser(self, context=None, **kwargs) -> Cmd2ArgumentParser:
        """Create `Cmd2ArgumentParser` for the command in provided context

        Args:
            context: A context to parse the command meta and retrieve the ArgParser

        Returns:
            Cmd2ArgumentParser
        """
        attributes = self._get_argparser_attributes(context)
        return CommandHelper.create_argparser_with_attributes(**(kwargs | attributes))
