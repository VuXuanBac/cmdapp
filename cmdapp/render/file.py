import io, re
import csv, json, yaml

from ..utils import Json, Hash, Platform


class FileFormat:
    def rename_records(data: list[dict], fieldnames: dict[str, str]):
        renamed_data = []
        for record in data:
            renamed_data.append(
                {rename: record.get(key) for key, rename in fieldnames.items()}
                | {k: v for k, v in record.items() if k not in fieldnames}
            )
        return renamed_data

    @classmethod
    def support_file_format(cls):
        attributes = dir(cls)
        method_prefix = "write_"
        return [
            key[len(method_prefix) :]
            for key in attributes
            if key.startswith(method_prefix)
        ]

    def write_csv(data: list[dict], file=None, options: dict = {}) -> str:
        """Write list of data item into CSV format.

        Args:
            - data (list[dict]): Data to render
            - file (io, optional): File to save result. Defaults to None (return string)
            - options (dict, optional): Format options for CSV, with following keys. Defaults to {}.
                - headers (bool): False to not generate headers. Default to True
                - delimiter (str): Field separator. Default to ','
                - quotechar (str): For quote value that contains special characters (like delimiter). Default to "'"
                - strict (bool): True to raise errors on input. Default to False
                - restval (Any): Default value for missing key. Default to ""
                - rename (dict[str, str]): Text to override key name. The keys order is important

        Returns:
            str: Formatted data
        """
        destination = file or io.StringIO(newline="")
        headers = options.pop("headers", True)
        fieldnames = list(data[0].keys())
        if headers:
            rename = options.pop("rename", {}) or {}
            if rename:
                # order in rename has higher priority
                fieldnames = list(rename) + [v for v in fieldnames if v not in rename]
        options = Hash.get_as_dict(
            options,
            delimiter=",",  # field separator
            quotechar='"',  # for quote value that contains special characters
            strict=False,  # ignore errors on input
            restval="",
        )

        writer = csv.DictWriter(destination, fieldnames, **options)
        if headers:
            writer.writerow({k: rename.get(k, k) for k in fieldnames})
        writer.writerows(data)
        return None if file else destination.getvalue()

    def write_json(data: list[dict], file=None, options: dict = {}) -> str:
        """Write list of data item into JSON format.

        Args:
            - data (list[dict]): Data to render
            - file (io, optional): File to save result. Defaults to None (return string)
            - options (dict, optional): Format options for JSON, with following keys. Defaults to {}.
                - skipkeys (bool): True to ignore error on keys that are not Python basic types.
                - indent (int): Indent space for pretty print
                - ensure_ascii (bool): True if the data is all ASCII, or else (if unicode) they are converted to ASCII
                - separators (tuple[str, str]): (item_separator, key-value_separator). Default to (", ", ": ")
                - sort_keys (bool): True to sort keys on same level
                - rename (dict[str, str]): Text to override key name. The keys order is important

        Returns:
            str: Formatted data
        """
        rename = options.pop("rename", None)
        if rename:
            data = FileFormat.rename_records(data, rename)
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

    def write_yaml(data: list[dict], file=None, options: dict = {}) -> str:
        """Write list of data item into YAML format.

        Args:
            - data (list[dict]): Data to render
            - file (io, optional): File to save result. Defaults to None (return string)
            - options (dict, optional): Format options for YAML, with following keys. Defaults to {}.
                - default_flow_style (bool): True to use flow style, or else (False) use block style. Default to False
                - indent (int): Indent space for pretty print
                - allow_unicode (bool): True if the data should be encode with unicode
                - sort_keys (bool): True to sort keys on same level
                - rename (dict[str, str]): Text to override key name. The keys order is important

        Returns:
            str: Formatted data
        """
        rename = options.pop("rename", None)
        if rename:
            data = FileFormat.rename_records(data, rename)
        options = Hash.get_as_dict(
            options,
            default_flow_style=False,  # False to always use block style (new line for each fields)
            indent=None,  # use that best for compact
            allow_unicode=True,
            sort_keys=False,  # sort keys on same level
        )
        return yaml.dump(data, file, **options)

    def write_html(data: list[dict], file=None, options: dict = {}) -> str:
        """Write list of data item into HTML table. HTML table format is customized by `options`

        Args:
            - data (list[dict]): Data to render
            - file (io, optional): File to save result. Defaults to None (return string)
            - options (dict, optional): Format options for HTML, with following keys. Defaults to {}.
                - template (str): Template in html format, placeholders are placed inside `{{<placeholder>}}`. If not provided, use custom template, it provides some css and js to sort
                - title (str): Page title and header
                - description (str): Description for the table data
                - rename (dict[str, str]): Text to override key name. The keys order is important
                - restval (Any): Default value for missing key. Default to ""
                - header_attributes (str): Html attributes to populated into `<th>` elements. Default: 'onclick="headerOnClick(this)"'
                - cell_attributes (str): Html attributes to populated into `<td>` elements. Default ''
                - kwargs (str): Data to populated into the template

        Returns:
            str: Formatted data
        """
        # parse options
        rename = options.pop("rename", {})
        restval = options.pop("restval", "")
        header_attributes = options.pop(
            "header_attributes", 'onclick="headerOnClick(this)"'
        )
        cell_attributes = options.pop("cell_attributes", "")
        template = options.pop("template", None)
        title = options.pop("title", "")
        description = (options.pop("description", "") or "").replace("\n", "<br/>")
        if not template:
            template_path = Platform.relpath("template.html", __file__)
            with open(template_path, "r") as template_file:
                template = template_file.read()
        # render data
        raw_headers = list(data[0].keys())
        if rename:
            renamed_headers = list(rename.values()) + [
                v for v in raw_headers if v not in rename
            ]
        else:
            renamed_headers = raw_headers
        header_html = "".join(
            [f"<th {header_attributes}>{header}</th>" for header in renamed_headers]
        )

        body_html = "".join(
            [
                f"<tr>{''.join([f'<td {cell_attributes}>{row.get(key, restval)}</td>' for key in raw_headers])}</tr>"
                for row in data
            ]
        )
        populate_data = options | dict(
            title=title, description=description, header=header_html, body=body_html
        )
        html_content = re.sub(
            r"{{(.*?)}}",
            lambda match: populate_data.get(match.group(1), match.group(0)),
            template,
        )
        if not file:
            return html_content
        file.write(html_content)
        return None
