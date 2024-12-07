import re
from ..types import DTypes
from ..utils import Hash

## Notes on case `) :` inside `datatype` part, it will be considered as comment.
ANNOTATION_PATTERN = r"^(?:\[\s*(\w+)\s*\])?([^():]*?)(?:\((.+?)\))?\s*(?::([\s\S]+))?$"
################# <flags> (<datatype>): <comment>
ANNOTATION_DATATYPE_PATTERN = (
    r"^(\*?\w+)(?:\[(\w+)\])?(?::\s*(\[.+?\]))?\s*(?:=\s*(.+))?$"
)


class AnnotationParser:
    """Support define fields by string with following format: `<flags> (<datatype>): <comment>`
    where:
    - flags (Optional): List of flags, separated by comma (,) or special character "*" for positional argument
    - datatype (Optional, wrapped by parentheses): In following format: (<* if required><dtype>[<proc>]: [<choices>] = <default_value>)
    - comment (Optional, prepended by a colon - :): Any text for comment
    """

    def _parse_flags(flags: str):
        if not flags or flags.isspace():
            return None
        flags = flags.strip()
        # positional
        if flags == "*":
            return []
        return [f.strip() for f in flags.split(",")]

    def _parse_datatype(datatype: str):
        if not datatype:
            return {}
        match_datatype: re.Match = re.match(
            ANNOTATION_DATATYPE_PATTERN, datatype.strip()
        )
        if not match_datatype:
            raise ValueError(
                f"annotation [{datatype}] has invalid format",
                f"expect [{ANNOTATION_DATATYPE_PATTERN}]",
            )

        dtype, proc, choices, default_value = match_datatype.groups()

        required = dtype[0] == "*"
        if required:
            dtype = dtype[1:]
        if choices:
            choices = DTypes.cast(choices, "array")
        if default_value:
            default_value = DTypes.cast(default_value, dtype)
        return dict(
            dtype=dtype,
            proc=proc,
            choices=choices,
            default=default_value,
            required=required or None,  # ignore if False
        )

    @staticmethod
    def parse(annotation: str) -> dict:
        """Parse annotation into Field metadata

        Args:
            annotation (str): Annotation to define the field

        Returns:
            dict: Field metadata
        """
        match_anno: re.Match = re.match(ANNOTATION_PATTERN, annotation)
        if not match_anno:
            return {}

        metavar, flags, datatype, comment = match_anno.groups()

        result = dict(
            flags=AnnotationParser._parse_flags(flags),
            comment=comment.strip() if comment else None,
            metavar=metavar,
        ) | AnnotationParser._parse_datatype(datatype)
        return Hash.remove(result, None)
