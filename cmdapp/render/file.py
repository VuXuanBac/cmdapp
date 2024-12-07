import io
import csv, json, yaml

from ..utils import Json, Hash


class FileFormat:
    @classmethod
    def support_file_format(cls):
        attributes = dir(cls)
        method_prefix = "write_"
        return [
            key[len(method_prefix) :]
            for key in attributes
            if key.startswith(method_prefix)
        ]

    def write_csv(data: list[dict], file=None, options: dict = {}):
        destination = file or io.StringIO(newline="")
        headers = options.setdefault("headers", True)
        options = Hash.get_as_dict(
            options,
            delimiter=",",  # field separator
            quotechar='"',  # for quote value that contains special characters
            strict=False,  # ignore errors on input
        )
        options.setdefault("fieldnames", list(data[0]))
        writer = csv.DictWriter(destination, **options)
        if headers:
            writer.writeheader()
        writer.writerows(data)
        return None if file else destination.getvalue()

    def write_json(data: list[dict], file=None, options: dict = {}):
        options = Hash.get_as_dict(
            options,
            skipkeys=False,  # ignore error on keys are not Python basic types
            indent=None,  # use that best for compact
            ensure_ascii=False,  # not escape to ascii
            separators=(", ", ": "),  # (item_separator, key-value_separator)
            sort_keys=False,  # sort keys on same level
        )
        options["default"] = Json.serializer
        return json.dump(data, file, **options) if file else json.dumps(data, **options)

    def write_yaml(data: list[dict], file=None, options: dict = {}):
        options = Hash.get_as_dict(
            options,
            default_flow_style=False,  # False to always use block style (new line for each fields)
            indent=None,  # use that best for compact
            allow_unicode=None,
            sort_keys=False,  # sort keys on same level
        )
        return yaml.dump(data, file, **options)
