from typing import Callable

from .app import CmdApp


class Response:
    def __init__(self, app: CmdApp):
        self.data = []
        self.app = app
        self.handler = app.poutput

    def on(self, handler: str | Callable):
        if isinstance(handler, str):
            handler = getattr(self.app, f"p{handler}", None)
        if callable(handler):
            self.handler = handler
        return self

    def __getattr__(self, name: str):
        formatter = getattr(self.app.response_formatter, name, None)
        if not name.startswith("_") and callable(formatter):

            def format(*args, **kwargs):
                formatted_data = formatter(*args, **kwargs)
                self.data.append(formatted_data)
                return self.send(formatted_data) if formatted_data else self

            return format
        else:
            return None

    def send(self, *args, **kwargs):
        self.handler(*args, **kwargs)
        return self

    def concat(self, response: "Response"):
        if response:
            self.data.extend(response.data)
        return self

    # @classmethod
    # def register_formatter(cls, formatter: ResponseFormatter, prefix: str = None):
    #     _formatters = [name for name in dir(formatter) if not name.startswith("__")]

    #     for name in _formatters:
    #         if prefix:
    #             name = prefix + name
    #         if hasattr(cls, name):
    #             raise ValueError(
    #                 f"the attribute [{name}] has been used on [{cls.__class__}]",
    #                 "try another name for setting",
    #             )
    #         method = getattr(formatter, name, None)
    #         if not callable(method):
    #             continue

    #         def _method(this: Response, *args, **kwargs):
    #             data = method(*args, **kwargs)
    #             if data:
    #                 if this.handler:
    #                     this.raw.append((this.handler, data))
    #                 else:
    #                     this.data = data
    #             return this

    #         setattr(cls, name, method)
