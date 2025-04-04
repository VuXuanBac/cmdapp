import re


class Sanitizer:
    def as_identifier(name: str) -> str:
        return re.sub(r"^\d|[^\w_]", "_", str(name))
