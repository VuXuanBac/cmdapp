from .template import Template
from .table import Tabling
from .file import FileFormat


class Response:
    def message(template: Template, *args, **kwargs):
        return template.format(*args, **kwargs)

    def table(data: list[dict], style="Simple", widths=None, headers=None):
        return Tabling.generate(data, style=style, widths=widths, headers=headers)

    def file(
        data: list[dict],
        format: str = "json",
        path: str = None,
        append: str = False,
        **kwargs,
    ):
        format = format or "json"
        renderer = getattr(FileFormat, f"write_{format}", None)
        if path:
            file = open(
                path,
                "a" if append else "w",
                newline="",
                encoding="utf-8",
            )
            formatted_data = renderer(data, file, kwargs)
        else:
            formatted_data = renderer(data, None, kwargs)
        return formatted_data

    # @classmethod
    # def register_renderer(cls, renderer_class, name: str = None, *args, **kwargs):
    #     if not issubclass(renderer_class, Renderer):
    #         return False
    #     name = name or renderer_class.__name__[: -len(Renderer.__name__)]
    #     method_name = f"render_{Text.to_snake_case(name)}"
    #     if hasattr(cls, method_name):
    #         return False
    #     renderer = renderer_class(*args, **kwargs)

    #     def render(self, *args, **kwargs):
    #         result = renderer.render(*args, **kwargs)
    #         return self.handler(result) if callable(self.handler) else result

    #     setattr(cls, method_name, render)
    #     return True
