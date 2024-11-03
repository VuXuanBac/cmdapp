from ..render import Response, FileFormat
from ..parser import COLUMN_ID, COLUMN_CREATE, COLUMN_UPDATE, COLUMN_DELETE
from ..database import Table, SQLCondition, SQLOperators
from ..core import Prototype, as_command
from ..utils import Platform, Hash, Text, Json
from .message import TEMPLATES


def get_arguments_for_table(table: Table, option: str):
    ignore_columns = [COLUMN_CREATE, COLUMN_UPDATE, COLUMN_DELETE]
    columns_metadata = {
        k: v.metadata for k, v in table.columns.items() if k not in ignore_columns
    }
    result_columns = {}
    if option == "add":
        result_columns = columns_metadata
        result_columns.pop(COLUMN_ID)
    elif option == "update":
        result_columns = {
            k: v | {"required": False} for k, v in columns_metadata.items()
        }
        result_columns[COLUMN_ID] |= {"flags": []}
    elif option == "delete":
        result_columns[COLUMN_ID] = columns_metadata[COLUMN_ID] | {
            "flags": [],  # positional
            "nargs": "+",
        }

    return result_columns


def get_value_parser(value: str, table: Table):
    return Text.translate(
        value, {"records": table.display_name(2), "record": table.display_name(1)}
    )


class BasePrototype(Prototype):
    @as_command(
        description="Create new record",
        dependencies={
            "type": "table",
            "arguments": lambda table: get_arguments_for_table(table, "add"),
            "parser": get_value_parser,
        },
    )
    def do_add(app, args, *, table: Table):
        attributes = vars(args)
        success = table.insert(attributes)
        message_kwargs = dict(
            action="CREATE", what=table.name, result=f"{success}/1 were created"
        )
        if success > 0:
            app.poutput(Response.message(TEMPLATES["success"], **message_kwargs))
        else:
            app.perror(Response.message(TEMPLATES["error"], **message_kwargs))
            app.print_database_errors()

    @as_command(
        description="Update an existing record",
        epilog="Using `--no-<column_name>` to set column to null",
        custom=True,
        dependencies={
            "type": "table",
            "arguments": lambda table: get_arguments_for_table(table, "update"),
            "parser": get_value_parser,
        },
    )
    def do_update(app, args, custom_values: list[str], *, table: Table):
        attributes = {}
        for key in custom_values:
            if key.startswith("--no-"):
                # if table.table_meta.is_require(key[5:]):
                #     app.perror(
                #         Response.message(
                #             TEMPLATES["argument_warning"],
                #             argument=key,
                #             status="invalid",
                #             reason=f"the corresponded column [{key[5:]}] can not be NULL",
                #             result=f"IGNORE [{key}]",
                #         )
                #     )
                # else:
                attributes[key[5:]] = None
        for key, value in vars(args).items():
            if key in table and value is not None:
                attributes[key] = value

        if len(attributes) == 1:  # only id
            app.perror(
                Response.message(
                    TEMPLATES["argument_warning"],
                    status="empty",
                    result="Skip updating",
                )
            )
            return

        success = table.update(attributes)
        message_kwargs = dict(
            action="UPDATE", what=table.name, result=f"{success}/1 were updated"
        )
        if success:
            app.poutput(Response.message(TEMPLATES["success"], **message_kwargs))
        else:
            app.perror(
                Response.message(
                    TEMPLATES["error"],
                    argument=COLUMN_ID,
                    value=attributes.get(COLUMN_ID, None),
                    **message_kwargs,
                )
            )
            app.print_database_errors()

    @as_command(
        description=f"Delete one or many records with {COLUMN_ID}s",
        arguments={"permanent": "p (bool = 0): set to delete permanently"},
        dependencies={
            "type": "table",
            "arguments": lambda table: get_arguments_for_table(table, "delete"),
            "parser": get_value_parser,
        },
    )
    def do_delete(app, args, *, table: Table):
        ids, permanent = Hash.get(vars(args), id=[], permanent=False)
        # search on deleted items if permanent is True
        existed_ids = table.which_exists(*ids, with_deleted=permanent)
        count = len(existed_ids)
        app.poutput(
            Response.message(
                TEMPLATES["found_info"],
                count=count,
                what=table.display_name(count),
                field=COLUMN_ID.upper(),
                items=existed_ids,
            )
        )
        success = (
            table.delete_by_id(*ids, permanent=permanent) if existed_ids else False
        )
        message_kwargs = dict(
            action="DELETE", what=table.name, result=f"{success}/{count} were deleted"
        )
        if success:
            app.poutput(Response.message(TEMPLATES["success"], **message_kwargs))
        else:
            app.perror(
                Response.message(
                    TEMPLATES["error"],
                    argument=COLUMN_ID,
                    value=ids,
                    **message_kwargs,
                )
            )
            app.print_database_errors()

    @as_command(
        description="Print all records and format as table",
        arguments={
            "format": "f (int: [0, 1, 2] = 1): table style: [0: no bordered], [1: bordered], [2: row alternating]",
            "widths": "w (array[int]): set width scale to the column, in display order. the column with width=2 is twice wider than column with width=1",
            "size": "s (int = 20): number of records per each page",
            "page": "p (int = 1): page index (based 1)",
            "columns": f'* (array[str] = ["^meta", "{COLUMN_ID}"]): columns to extract data',
            "all": "a (bool = 0): set to include deleted records",
        },
        dependencies={
            "type": "table",
            "parser": get_value_parser,
        },
    )
    def do_list(app, args, *, table: Table):
        column_filters, format, widths, page_size, page_index, with_deleted = Hash.get(
            vars(args),
            columns=["^meta", COLUMN_ID],
            format=0,
            widths=[],
            size=None,
            page=1,
            all=False,
        )
        if page_size < 0:
            page_size = None
        if page_index <= 0:
            page_index = 1

        condition = (
            None if with_deleted else SQLCondition(COLUMN_DELETE, SQLOperators.IS_NULL)
        )
        all_items = table.query(
            columns=column_filters,
            condition=condition,
            page_size=page_size,
            page_index=page_index,
        )
        count = len(all_items)
        if count == 0:
            app.poutput(
                Response.message(
                    TEMPLATES["found_info"],
                    negative=True,
                    what=table.display_name(count),
                )
            )
            return

        app.poutput(
            Response.message(
                TEMPLATES["found_info"],
                count=count,
                total=page_size,
                what=table.display_name(count),
            )
        )
        app.poutput(Response.table(data=all_items, style=format, widths=widths))
        if page_size:
            app.poutput(
                Response.message(
                    TEMPLATES["info"],
                    f"PAGE {page_index} - {table.display_name(page_size).upper()}_PER_PAGE: {page_size}",
                )
            )

    @as_command(
        description="Get all records and save them in one or many file format",
        epilog="You can use redirection > (write) or >> (append) to save result to file.",
        arguments={
            "columns": "* (array[str] = *): columns to export",
            "format": f"f (*str: {Json.dump(FileFormat.support_file_format())}): file format to export",
            "path": "p (str): path to the file to write data to",
            "append": "a (bool = 0): [Path] set to open file in append mode instead of write mode",
            "headers": "(bool = 1): [CSV] set to not render headers",
            "indent": "(int): [JSON, YAML] number of whitespaces for indentation at each level",
            "sort": "(bool = 0): [JSON, YAML] set to sort keys on same level",
        },
        dependencies={
            "type": "table",
            "parser": get_value_parser,
        },
    )
    def do_export(app, args, *, table: Table):
        format, column_filters = Hash.get(vars(args), format=False, columns=[])

        all_items = table.query(columns=column_filters)
        count = len(all_items)
        if count == 0:
            app.poutput(
                Response.message(
                    TEMPLATES["found_info"],
                    negative=True,
                    what=table.display_name(count),
                )
            )
            return

        app.poutput(
            Response.message(
                TEMPLATES["found_info"], count=count, what=table.display_name(count)
            )
        )
        options = Hash.ignore(vars(args), "format", "columns", sort="sort_keys")

        path = options.get("path", None)
        if path and options.get("append", False) and not Platform.isfile(path):
            app.poutput(
                Response.message(
                    TEMPLATES["argument_warning"],
                    argument="--path",
                    status="invalid",
                    reason="it is not a file path",
                    result="IGNORE [path] argument",
                )
            )
            path = None
        if not path:
            options.pop("path")
            app.ppaged(Response.file(all_items, format=format, **options))
        else:
            Response.file(all_items, format=format, **options)
            app.poutput(
                Response.message(
                    TEMPLATES["success"],
                    action="EXPORT",
                    what=table.name,
                    result=f"Check the file at [{Platform.abs(path)}]",
                )
            )
