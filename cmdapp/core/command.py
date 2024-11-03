from cmd2 import Cmd2ArgumentParser, with_argparser
from typing import Callable

from ..utils import Hash


class CommandBuilder:
    def create_command(
        name: str,
        handler: Callable,
        argparser: Cmd2ArgumentParser,
        with_argparser_options: dict,
        **kwargs,
    ) -> Callable:
        """Create a command.

        Args:
            command_name (str): Command name
            method (Callable): Command logic method
            argparser (Cmd2ArgumentParser): Argparser for creating the command
            options (dict[str, dict]): Options for creating the command.
            kwargs: Arguments passed to `handler`

        Returns:
            Callable: A method represent the command
        """
        if not argparser:
            return None

        def command(*args):
            handler(*args, **kwargs)

        command.__name__ = f"do_{name}"
        return with_argparser(argparser, **with_argparser_options)(command)

    def create_placeholder_command(
        name: str,
        derived_command_names: list[str],
        argument_name: str,
        default_derived_command: str = None,
        *,
        description: str = "",
        epilog: str = "",
        **kwargs,
    ) -> Callable:
        """When many commands has same logic (prototype), they can be designed as subcommands like "create user", "create team", "create <anything>",...
        Subcommands should be hidden and introduced by another command, this command is called placeholder command (or parent command).
        This method used to create placeholder command (or parent command, like "create")

        Args:
            name (str): Name of placeholder command
            derived_command_names (list[str]): List of subcommand name
            argument_name (str): Name of argument for placeholder command
            default_derived_command (str, optional): Name of default subcommand if argument was not set. Defaults to None.
            description (str): Description to create placeholder command argparser
            epilog (str): Epilog to create placeholder command argparser. This will be append introduces text for derived commands
            kwargs: Arguments to create placeholder command argparser

        Returns:
            Callable: Created command with decorated arguments
        """
        if not derived_command_names:
            return None
        epilog_extra = [
            f"{name} {derived_name}" for derived_name in derived_command_names
        ]
        epilog_extra = f"[{'], ['.join(epilog_extra)}]"

        argparser = Cmd2ArgumentParser(
            description=description,
            epilog=f"{epilog}\n{'='*80}\nSee following commands: {epilog_extra}",
            add_help=False,
            **Hash.ignore(kwargs, "description", "epilog", "add_help"),
        )
        argparser.add_argument(
            argument_name,
            type=str,
            choices=derived_command_names,
            default=default_derived_command,
        )
        # argparser.add_argument("-h", "--help", action="help")

        def command(app, args, subargs):
            derived_name = getattr(args, argument_name, default_derived_command)
            # if derived_name == "-h" or derived_name == "--help":
            #     return app.print_help()
            method = getattr(app, f"do_{name}_{derived_name}", None)
            if method:
                return method(" ".join(subargs))

        command.__name__ = f"do_{name}"
        return with_argparser(argparser, with_unknown_args=True, preserve_quotes=True)(
            command
        )
