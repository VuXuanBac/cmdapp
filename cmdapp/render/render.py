from typing import Callable
from .template import Template, TemplateParser
from .table import Tabling
from .file import FileFormat
from functools import partial

DEFAULT_STYLES = {"success": "/G", "error": "/*R", "warning": "/Y", "info": "/b"}


class ResponseFormatter:
    def __init__(
        self,
        templates: dict[str, Template] = None,
        styles: dict[str, dict] = None,
        file_format_cls=None,
    ):
        self.templates = templates or {}
        styles = styles or DEFAULT_STYLES
        self.styles = {}
        for name, format in styles.items():
            if isinstance(format, str):
                format = TemplateParser.parse_format(format, {})
            if isinstance(format, dict):
                self.styles[name] = format
        self._import_from_file_formatter(file_format_cls or FileFormat)

    def message(self, template: str | Template, *args, **kwargs):
        if not isinstance(template, Template):
            template = self.templates.get(template, None)
        style = kwargs.get("style")
        if template is None:
            message = " ".join([str(arg) for arg in args])
        else:
            message = template.format(*args, **kwargs)
        if not isinstance(style, dict):
            style = self.styles.get(style, None)
        if isinstance(style, dict):
            return Template.apply_format(message, **style)
        return message

    def table(self, data: list[dict], style="Simple", widths=None, headers=None):
        return Tabling.generate(data, style=style, widths=widths, headers=headers)

    def _file(
        data: list[dict],
        path: str = None,
        append: str = False,
        formatter: Callable = None,
        **kwargs,
    ):
        if path:
            file = open(path, "a" if append else "w", newline="", encoding="utf-8")
            formatted_data = formatter(data, file, kwargs)
        else:
            formatted_data = formatter(data, None, kwargs)
        return formatted_data

    def _import_from_file_formatter(self, cls):
        file_formatter = cls if issubclass(cls, FileFormat) else FileFormat
        self.support_file_formats = file_formatter.support_file_format()
        for format in self.support_file_formats:

            renderer = getattr(file_formatter, f"write_{format}", None)

            setattr(self, format, partial(self.__class__._file, formatter=renderer))
