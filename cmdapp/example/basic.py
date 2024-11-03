from cmdapp.core import start_app, CmdApp, as_command, Prototype
from cmdapp.render import Response, Template
from datetime import datetime


class CustomPrototype(Prototype):
    @as_command(
        description="Print message with style and color",
        arguments={
            "template": "* (str): format string",
            "destination": 'to, o (str: ["stdout", "stderr"] = stdout): send to stdout or stderr',
        },
        custom=True,
    )
    def do_message(app: CmdApp, args, custom: list[str]):
        template = Template(args.template)
        destination = args.destination
        method = app.poutput if destination == "stdout" else app.perror
        _args, _kwargs = [], {}
        keyword = None
        for item in custom:
            if item.startswith("-"):
                keyword = item.strip("-").replace("-", "_")
            else:
                if keyword:
                    _kwargs[keyword] = item
                    keyword = None
                else:
                    _args.append(item)
        method(Response.message(template, *_args, **_kwargs))

    @as_command(description="Echo datetime and system info")
    def do_now(app: CmdApp, args):
        template = Template("+[Now: ]*/M[{timestamp}]")
        app.poutput(Response.message(template, timestamp=datetime.now()))


if __name__ == "__main__":
    start_app(
        app_name="Assistant",
        app_class=CmdApp,
        app_prototypes=CustomPrototype(),
    )
