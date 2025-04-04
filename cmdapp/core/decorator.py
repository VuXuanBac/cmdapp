from ..parser import CommandMeta
from .prototype import COMMAND_ATTRIBUTE_FOR_PROTOTYPE


def as_command(
    description: str = None,
    epilog: str = None,
    arguments: dict = None,
    category: str = None,
    custom: bool = False,
    dependencies: dict = None,
):
    def decorator(func):
        command_meta = CommandMeta(
            description=description,
            epilog=epilog,
            arguments=arguments,
            dependencies=dependencies,
            custom=custom,
            category=category,
        )

        setattr(func, COMMAND_ATTRIBUTE_FOR_PROTOTYPE, command_meta)

        return func

    return decorator
