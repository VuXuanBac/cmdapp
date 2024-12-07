from ..parser import COLUMN_ID, COLUMN_CREATE, COLUMN_UPDATE, COLUMN_DELETE
from ..database import Database, Table, SQLCondition, SQLOperators
from ..core import Prototype, as_command, ContextStore, Response
from ..utils import Platform, Hash, Text
from .app import BaseApp


class BasePrototype(Prototype):

    def __init__(self, database: Database, category=None):
        database_as_context_store = ContextStore(
            "table", {table.human_name(1): table for table in database.tables.values()}
        )
        super().__init__(database_as_context_store, category)

    def get_table_arguments(self, command: str, table_columns: dict):
        ignore_columns = [COLUMN_CREATE, COLUMN_UPDATE, COLUMN_DELETE]
        columns_metadata = {
            k: v.metadata for k, v in table_columns.items() if k not in ignore_columns
        }
        result_columns = {}
        if command == "create":
            result_columns = columns_metadata
            result_columns.pop(COLUMN_ID)
        elif command == "update":
            result_columns = {
                k: v | {"required": False} for k, v in columns_metadata.items()
            }
            result_columns[COLUMN_ID] |= {"flags": []}
        elif command == "delete":
            result_columns[COLUMN_ID] = columns_metadata[COLUMN_ID] | {
                "flags": [],  # positional
                "nargs": "+",
            }

        return result_columns

    def contexted_arguments_creator(self, context: str, command: str) -> dict | None:
        table: Table = self.context_store.get_context_data(context)
        if table:
            return self.get_table_arguments(command, table.table_meta.columns)

    def contexted_value_parser(
        self, context: str, value: str, command: str = None
    ) -> str:
        table: Table = self.context_store.get_context_data(context)
        return Text.translate(
            value, {"records": table.human_name(2), "record": table.human_name(1)}
        )

    def print_database_errors(app: BaseApp):
        errors = app.database.get_errors()
        if not app.debug or not errors:
            return None
        response = Response(app).on("error").send("-" * 80)
        for error in errors:
            response.message(
                "exception",
                type=error["type"],
                message=error["message"],
                command=error["sql"],
                argument=error["data"],
            )
            response.send("-" * 80)
        return response

    @as_command(description="Create new record", dependencies="*")
    def do_create(app, args, *, table: Table):
        attributes = vars(args)
        success = table.insert(attributes)
        message_kwargs = dict(
            action="CREATE", what=table.name, result=f"{success}/1 were created"
        )
        if success > 0:
            return Response(app).message("success", **message_kwargs)
        else:
            return (
                Response(app)
                .on("error")
                .message("error", **message_kwargs)
                .concat(BasePrototype.print_database_errors(app))
            )

    @as_command(
        description="Update an existing record",
        epilog="Using `--no-<column_name>` to set column to null",
        custom=True,
        dependencies="*",
    )
    def do_update(app, args, custom_values: list[str], *, table: Table):
        attributes = {}
        for key in custom_values:
            if key.startswith("--no-"):
                # if table.table_meta.is_require(key[5:]):
                #         Response(app).on("error").message(
                #             "argument_warning",
                #             argument=key,
                #             status="invalid",
                #             reason=f"the corresponded column [{key[5:]}] can not be NULL",
                #             result=f"IGNORE [{key}]",
                #         )
                # else:
                attributes[key[5:]] = None
        for key, value in vars(args).items():
            if key in table and value is not None:
                attributes[key] = value

        if len(attributes) == 1:  # only id
            return (
                Response(app)
                .on("error")
                .message("argument_warning", status="empty", result="Skip updating")
            )

        success = table.update(attributes)
        message_kwargs = dict(
            action="UPDATE", what=table.name, result=f"{success}/1 were updated"
        )
        if success:
            return Response(app).message("success", **message_kwargs)
        else:
            return (
                Response(app)
                .on("error")
                .message(
                    "error",
                    argument=COLUMN_ID,
                    value=attributes.get(COLUMN_ID, None),
                    **message_kwargs,
                )
                .concat(BasePrototype.print_database_errors(app))
            )

    @as_command(
        description=f"Delete one or many records with {COLUMN_ID}s",
        arguments={"permanent": "p (bool = 0): set to delete permanently"},
        dependencies="*",
    )
    def do_delete(app, args, *, table: Table):
        ids, permanent = Hash.get(vars(args), id=[], permanent=False)
        # search on deleted items if permanent is True
        existed_ids = table.which_exists(*ids, with_deleted=permanent)
        count = len(existed_ids)
        response = Response(app).message(
            "found",
            count=count,
            what=table.human_name(count),
            field=COLUMN_ID.upper(),
            items=existed_ids,
        )
        if not existed_ids:
            return response
        success = table.delete_by_id(*ids, permanent=permanent)
        message_kwargs = dict(
            action="DELETE", what=table.name, result=f"{success}/{count} were deleted"
        )
        if success:
            return response.message("success", **message_kwargs)
        else:
            return (
                response.on("error")
                .message("error", argument=COLUMN_ID, value=ids, **message_kwargs)
                .concat(BasePrototype.print_database_errors(app))
            )

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
        dependencies="*",
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
            return Response(app).message(
                "found", negative=True, what=table.human_name(count)
            )

        response = (
            Response(app)
            .message(
                "found", count=count, total=page_size, what=table.human_name(count)
            )
            .table(data=all_items, style=format, widths=widths)
        )
        if page_size:
            response.message(
                "info",
                f"PAGE {page_index} - {table.human_name(page_size).upper()}_PER_PAGE: {page_size}",
            )
        return response

    @as_command(
        description="Get all records and save them in one or many file format",
        epilog="You can use redirection > (write) or >> (append) to save result to file.",
        arguments={
            "columns": "* (array[str] = *): columns to export",
            "format": f"f (*str): file format to export",
            "path": "p (str): path to the file to write data to",
            "append": "a (bool = 0): [Path] set to open file in append mode instead of write mode",
            "headers": "(bool = 1): [CSV] set to not render headers",
            "indent": "(int): [JSON, YAML] number of whitespaces for indentation at each level",
            "sort": "(bool = 0): [JSON, YAML] set to sort keys on same level",
        },
        dependencies="*",
    )
    def do_export(app, args, *, table: Table):
        format, column_filters = Hash.get(vars(args), format=False, columns=[])

        all_items = table.query(columns=column_filters)
        count = len(all_items)
        if count == 0:
            return Response(app).message(
                "found", negative=True, what=table.human_name(count)
            )

        response = Response(app).message(
            "found", count=count, what=table.human_name(count)
        )
        options = Hash.ignore(vars(args), "format", "columns", sort="sort_keys")

        path = options.get("path", None)
        if path and options.get("append", False) and not Platform.isfile(path):
            response.message(
                "argument_warning",
                argument="--path",
                status="invalid",
                reason="it is not a file path",
                result="IGNORE [path] argument",
            )
            path = None

        if not path:
            options.pop("path")
            return response.on("paged").__getattr__(format)(all_items, **options)
        else:
            return (
                response.on("output")
                .__getattr__(format)(all_items, **options)
                .message(
                    "success",
                    action="EXPORT",
                    what=table.name,
                    result=f"Check the file at [{Platform.abs(path)}]",
                )
            )
