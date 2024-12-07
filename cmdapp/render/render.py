from typing import Callable
from .template import Template
from .table import Tabling
from .file import FileFormat
from functools import partial


class ResponseFormatter:
    def __init__(self, templates: dict[str, Template] = None, file_format_cls=None):
        self.templates = templates or {}
        self._import_from_file_formatter(file_format_cls or FileFormat)

    def message(self, template: str | Template, *args, **kwargs):
        if not isinstance(template, Template):
            template = self.templates.get(template, None)
        if template is None:
            return " ".join([str(arg) for arg in args]) + " ".join(
                [str(v) for k, v in kwargs.items()]
            )
        return template.format(*args, **kwargs)

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
        for format in file_formatter.support_file_format():

            renderer = getattr(file_formatter, f"write_{format}", None)

            setattr(self, format, partial(self.__class__._file, formatter=renderer))
