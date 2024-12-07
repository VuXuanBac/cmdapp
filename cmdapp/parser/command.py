from typing import Callable
from cmd2 import Cmd2ArgumentParser
from .field import FieldMeta, FieldHelper


class CommandHelper:
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
        dependencies: list[str] = None,
        category: str = None,
        custom: bool = False,
    ) -> None:
        """CommandMeta store data to create application commands

        Args:
            description (str): Description text describe the command
            epilog (str): Text describe the command, display like a post script
            arguments (dict): Arguments of the command with key is the argument name and value is a str or dict that used to created a `FieldMeta`
            dependencies (list[str], optional): Specify contexts that the command prototype depends on. For each context, a subcommand will be created. The context can be used to parse custom arguments (for each subcommands) and parse text value (description, epilog, help...) corresponded to the context. Defaults to None.
            category (str, optional): Category for the command. Defaults to None.
            custom (bool, optional): True if the command accepts unknown arguments. Defaults to False.
        """
        self.description = description or ""
        self.epilog = epilog or ""
        self.arguments = arguments if isinstance(arguments, dict) else {}
        self.category = category or None
        self.with_argparser_options = dict(with_unknown_args=bool(custom))
        self.dependencies = dependencies or None

    def create_argparser(self, **kwargs) -> Cmd2ArgumentParser:
        """Create `Cmd2ArgumentParser` from command meta

        Args:
            kwargs: Options on creating Cmd2ArgumentParser

        Returns:
            Cmd2ArgumentParser
        """
        attributes = {
            "description": self.description,
            "epilog": self.epilog,
            "arguments": {
                name: FieldHelper.parse(metadata)
                for name, metadata in self.arguments.items()
            },  # avoid side effect
        }
        return CommandHelper.create_argparser_with_attributes(**(kwargs | attributes))

    def create_contexted_argparser(
        self,
        context: str,
        *,
        contexted_arguments_creator: Callable = None,
        contexted_value_parser: Callable = None,
        **kwargs,
    ) -> Cmd2ArgumentParser:
        """Create `Cmd2ArgumentParser` in provided context

        Args:
            context (str): Context to parse command meta
            contexted_arguments_creator (Callable, optional): Function to generate more arguments (contexted arguments). Defaults to None.
            contexted_value_parser (Callable, optional): Function to parse text value (like description, epilog, help,...). Defaults to None.

        Raises:
            ValueError: Error on generating contexted arguments

        Returns:
            Cmd2ArgumentParser:
        """
        arguments = self.arguments
        if callable(contexted_arguments_creator):
            contexted_arguments = contexted_arguments_creator(context) or {}
            if not isinstance(contexted_arguments, dict):
                raise ValueError(
                    f"get arguments for context {context} fail because the returned value {contexted_arguments} is not a dict"
                )
            # when context arguments confict name with normal arguments: normal argument has higher priority
            arguments = contexted_arguments | arguments
        attributes = {
            "description": self.description,
            "epilog": self.epilog,
            "arguments": {
                name: FieldHelper.parse(metadata)
                for name, metadata in arguments.items()
            },
        }
        if callable(contexted_value_parser):
            attributes["description"] = contexted_value_parser(
                context, attributes["description"]
            )
            attributes["epilog"] = contexted_value_parser(context, attributes["epilog"])
            for name, metadata in attributes["arguments"].items():
                if "comment" not in metadata:
                    continue
                metadata["comment"] = contexted_value_parser(
                    context, metadata["comment"]
                )
        return CommandHelper.create_argparser_with_attributes(**(kwargs | attributes))
