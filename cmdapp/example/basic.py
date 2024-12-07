from cmdapp.core import start_app, as_command, CmdApp, Prototype, Response
from cmdapp.render import Template
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
        dest = "output" if destination == "stdout" else "error"
        return Response(app).on(dest).message(template, *_args, **_kwargs)

    @as_command(description="Echo datetime and system info")
    def do_now(app: CmdApp, args):
        template = Template("+[Now: ]*/M[{timestamp}]")
        return Response(app).message(template, timestamp=datetime.now())


if __name__ == "__main__":
    start_app(
        app_name="Assistant",
        app_class=CmdApp,
        app_prototypes=CustomPrototype(),
    )
