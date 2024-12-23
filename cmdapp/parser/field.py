from ..utils import Hash
from ..types import SUPPORT_DTYPES, DTypes, DTYPE2TYPE
from .annotation import AnnotationParser
from .argparser_options import ArgParserOptions

FIELD_ATTRIBUTES_TYPES = dict(
    dtype=str,
    required=bool,
    default=None,  # depend on dtype
    default_value=None,  # alias for default
    comment=str,
    choices=list,
    # unique=bool, # should declare it as table constraints
    # positional=bool, # flags: None means positional
    flags=list,
    proc=str,
    nargs=(int, str),
    action=str,
    metavar=str,  # display object name on help message like --path PATH
    # const=None,  # depend on dtype
)

ACTION_ALLOW_VALUES = [
    "store",
    # "store_const",
    "append",
    # "extend",
    # "append_const",
    "count",
    "help",
    "version",
]


class FieldHelper:
    def sanitize_field(key: str, value):
        if value is None or key not in FIELD_ATTRIBUTES_TYPES:
            return None
        casted_value = DTypes.cast_with_converters(value, FIELD_ATTRIBUTES_TYPES[key])
        if key == "dtype":
            if casted_value not in SUPPORT_DTYPES:
                return "str"
        elif key == "choices":
            if not casted_value:
                return None
        elif key == "action":
            if casted_value not in ACTION_ALLOW_VALUES:
                return None
        elif key == "nargs":
            if isinstance(casted_value, str) and casted_value not in ["?", "*", "+"]:
                return None
        return casted_value

    @staticmethod
    def sanitize_metadata(metadata: dict) -> dict:
        options = {k: FieldHelper.sanitize_field(k, v) for k, v in metadata.items()}
        options = Hash.remove(options, None)

        dtype = options.setdefault("dtype", "str")

        if "default" in options:
            default_value = options.pop("default")
            options["default_value"] = DTypes.cast_with_converters(
                default_value, DTYPE2TYPE[dtype]
            )

        return options

    @staticmethod
    def parse(metadata: str | dict) -> dict:
        meta_dict = {}
        if isinstance(metadata, str):
            meta_dict = AnnotationParser.parse(metadata)
        elif isinstance(metadata, dict):
            annotation = metadata.get("annotation", None)
            if annotation:
                meta_dict = AnnotationParser.parse(annotation) | metadata
            else:
                meta_dict = metadata
        return meta_dict


class FieldMeta:

    def __init__(self, name: str, metadata: str | dict):
        # print(f"CREATE FieldMeta with name = {name}, metadata = {metadata}")
        self.name = name
        meta_dict = FieldHelper.parse(metadata)
        self.metadata = FieldHelper.sanitize_metadata(meta_dict)

    def as_argparser_argument(self) -> dict:
        return ArgParserOptions.from_metadata(self.name, self.metadata)

    def __contains__(self, key):
        return self.metadata.__contains__(key)

    def __getitem__(self, key):
        return self.metadata.get(key, None)

    def __setitem__(self, key, value):
        sanitized_value = FieldHelper.sanitize_field(key, value)
        if sanitized_value is not None:
            self.metadata[key] = sanitized_value
        return sanitized_value

    def __repr__(self) -> str:
        return str(dict(name=self.name, metadata=self.metadata))

    def __str__(self) -> str:
        return str(dict(name=self.name, metadata=self.metadata))

    def to_json(self) -> dict:
        return dict(name=self.name, metadata=self.metadata)
