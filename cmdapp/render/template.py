import re, copy
from cmd2 import ansi
from cmd2.utils import TextAlignment, align_text
from ..utils import Hash

INHERIT_CHAR = "&"
RESET_CHAR = "@"

TEXT_TO_ALIGN = {
    "=": TextAlignment.CENTER,
    ">": TextAlignment.RIGHT,
    "<": TextAlignment.LEFT,
}

TEXT_TO_STYLE = {
    "*": "bold",
    "/": "italic",
    "^": "overline",  # note that this is special character in [], so DONT put it at start
    "~": "strikethrough",
    "_": "underline",
    ".": "dim",
}

TEXT_TO_COLOR = {
    "x": "",
    "b": "LIGHT_BLUE",
    "c": "LIGHT_CYAN",
    "d": "LIGHT_GRAY",
    "k": "BLACK",
    "g": "LIGHT_GREEN",
    "m": "LIGHT_MAGENTA",
    "r": "LIGHT_RED",
    "w": "WHITE",
    "y": "LIGHT_YELLOW",
    "B": "BLUE",
    "C": "CYAN",
    "D": "DARK_GRAY",
    "K": "BLACK",
    "G": "GREEN",
    "M": "MAGENTA",
    "R": "RED",
    "W": "WHITE",
    "Y": "YELLOW",
}

TEXT_TO_TRANSFORM = {
    "!": str.capitalize,
    "#": str.title,
    "+": str.upper,
    "-": str.lower,  # note that this is special character in [], so put it at end
}

ALIGN_REGEX = rf"(\d*)([{''.join(TEXT_TO_ALIGN)}]?)"
STYLE_REGEX = rf"([{''.join(TEXT_TO_STYLE)}]*)"
COLOR_REGEX = rf"([{''.join(TEXT_TO_COLOR)}]{'{0,2}'})"
TRANSFORM_REGEX = rf"([{''.join(TEXT_TO_TRANSFORM)}]?)"

FORMAT_REGEX = f"^({INHERIT_CHAR}|{RESET_CHAR})?{ALIGN_REGEX}{STYLE_REGEX}{COLOR_REGEX}{TRANSFORM_REGEX}$"
PATTERN_REGEX = r"^([\s\S]+?)(?:\|([\w,]+))?$"
PLACEHOLDER_REGEX = r"(?<!\\)\{(\w+)\}"


class TemplateParser:

    # [Text only] => Always shown
    # [Truthy|suffix] => Shown only if `suffix` is in data. Truthy can contains any, but at least one character.
    # [With {argument}s and {argument}s] => Shown only if all argument are in data. This part depends on all `argument`
    @staticmethod
    def parse_pattern(pattern: str):
        if not pattern:
            return None
        match = re.match(PATTERN_REGEX, str(pattern))
        if not match:
            return None
        text, suffix = match.groups()
        dependencies = re.findall(PLACEHOLDER_REGEX, text)
        if suffix:
            dependencies += suffix.split(",")

        # make this not a placeholder for format
        text = re.sub(r"\\{(\w+)\\?\}|\{(\w+)\\\}", "{{\\1\\2}}", text)
        text = re.sub(r"\\(.)", "\\1", text)
        return text, dependencies

    @staticmethod
    def parse_format(format: str, base_format: dict):
        if not format or str(format).isspace():
            return None
        match = re.match(FORMAT_REGEX, str(format).strip())
        if not match:
            return None
        inherit_reset, align_width, align, style, colors, transform = match.groups()

        format_dict = (
            copy.deepcopy(base_format)
            if (inherit_reset == INHERIT_CHAR and base_format)
            else {}
        )
        ### Alignment
        if align:
            format_dict |= {
                "alignment": TEXT_TO_ALIGN[align],
                "width": int(align_width) if align_width else None,
            }

        if style:
            format_dict |= {
                TEXT_TO_STYLE[c]: (c in TEXT_TO_STYLE) or None for c in style
            }

        if transform:
            format_dict["transform"] = TEXT_TO_TRANSFORM.get(transform, None)

        if colors:
            fg, bg = (colors + "x")[:2]
            format_dict |= {
                "fg": getattr(ansi.Fg, TEXT_TO_COLOR[fg], None),
                "bg": getattr(ansi.Bg, TEXT_TO_COLOR[bg], None),
            }

        return Hash.remove(format_dict, None)

    @staticmethod
    def parse(template: str):
        parts = re.split(r"(?<!\\)([\[\]]+)", template + "]")
        obj = None
        base_format = None
        format_index = 0
        formats = [{}]
        patterns = {format_index: []}
        for part in parts:
            if not part:
                continue
            if part[0] == "[":
                format = TemplateParser.parse_format(obj, base_format)
                if format is not None:
                    base_format = format
                    formats.append(format)
                    format_index += 1
                    patterns[format_index] = []
            elif part[0] == "]":
                pattern = TemplateParser.parse_pattern(obj)
                if pattern:
                    patterns[format_index].append(pattern)
            else:
                obj = part

        return formats, patterns


class Template:
    def __init__(self, template: str):
        self.raw = template
        self.formats, self.patterns = TemplateParser.parse(template)

    def format(self, *args, **kwargs):
        result = ""

        arguments = {str(index): value for index, value in enumerate(args)} | kwargs
        for format_index, patterns in self.patterns.items():
            format_string = ""
            for pattern, dependencies in patterns:
                if all([kw in arguments for kw in dependencies]):
                    format_string += pattern
            if not format_string:
                continue
            populated_text = format_string.format(*args, **kwargs)
            result += __class__.apply_format(
                populated_text, **self.formats[format_index]
            )
        return result

    @staticmethod
    def apply_format(text: str, **kwargs):
        text = str(text)
        transform = kwargs.get("transform", None)
        if callable(transform):
            text = transform(text)

        alignment, align_width = Hash.get(kwargs, alignment=None, width=None)
        if alignment:
            text = align_text(
                text, alignment=alignment, fill_char=" ", width=align_width
            )
        styles = Hash.filter(
            kwargs,
            "fg",
            "bg",
            "bold",
            "italic",
            "dim",
            "underline",
            "overline",
            "strikethrough",
        )
        return ansi.style(text, **styles) if styles else text
