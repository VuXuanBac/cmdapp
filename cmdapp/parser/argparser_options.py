import re
from ..utils import Hash
from ..types import DTypes


class ArgParserOptions:
    def sanitize_flag(flag: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]", "-", flag).strip("-")

    @staticmethod
    def argparser_help(
        dtype: str = None,
        required: bool = None,
        default_value=None,
        comment: str = None,
    ) -> str:
        parts = []
        if dtype is not None:
            parts.append(f"[{dtype}]")
        if required:  # and dtype != "bool":
            parts.append("[not null]")
        if default_value is not None:
            parts.append(f"[=: {default_value}]")
        if comment:
            parts.append(comment)
        return " ".join(parts)

    @staticmethod
    def argparser_flags(name: str, flags: list = None):
        # positional
        if flags == []:
            return []
        flags = (flags or []) + [name]
        flags = [ArgParserOptions.sanitize_flag(flag) for flag in flags]
        return [f"{'-' if len(flag) == 1 else '--'}{flag}" for flag in flags if flag]

    @staticmethod
    def for_bool(name: str, options: dict) -> dict:
        default_value, comment = Hash.get(options, default_value=None, comment=None)
        flags = [f"--no-{name}"] if default_value else [f"--{name}"]
        help = ArgParserOptions.argparser_help(
            dtype="bool",
            default_value=default_value,
            comment=comment,
        )
        return dict(
            flags=flags,
            help=help,
            action=("store_false" if default_value else "store_true"),
            dest=name,
        )

    @staticmethod
    def from_metadata(name: str, metadata: dict) -> dict:
        if "dtype" not in metadata:
            raise ValueError(f"missing [dtype] for parsing argparser")
        dtype = metadata["dtype"]
        if dtype == "bool":
            return ArgParserOptions.for_bool(name, metadata)
        # Get flags
        flags = ArgParserOptions.argparser_flags(
            name, flags=metadata.get("flags", None)
        )
        is_positional = not bool(flags)
        # For string and array, support convert item dtype via `proc`
        subtype = (
            metadata.get("proc", "str") if dtype in ["str", "array", "json"] else dtype
        )
        type = DTypes.text_converter(subtype, dtype)

        help = ArgParserOptions.argparser_help(
            dtype=dtype,
            required=None if is_positional else metadata.get("required", None),
            default_value=metadata.get("default_value", None),
            comment=metadata.get("comment", None),
        )
        argparser_options: dict = Hash.filter(
            metadata,
            "required",
            "action",
            "choices",
            # "const",
            "nargs",
            default_value="default",
        ) | dict(dest=name, flags=flags, type=type, help=help)
        metavar = metadata.get("metavar", "").upper() or None
        if metavar:
            argparser_options["metavar"] = metavar
        # if argparser_options.get("default", None):
        #     argparser_options["required"] = False
        if is_positional:
            argparser_options.pop("required", None)
            if argparser_options.get("default", None):
                argparser_options.setdefault("nargs", "?")
        if dtype in ["json", "array"]:
            argparser_options.setdefault("nargs", "*")
        return argparser_options
