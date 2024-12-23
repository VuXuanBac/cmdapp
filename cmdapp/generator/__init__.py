from ..parser import TableMeta
from ..utils import Sanitizer
import json


def generate_schema(schema: list[TableMeta], output: str = None, format="python"):
    schema_dict = {}
    for table_meta in schema:
        metadata = table_meta.to_json()
        table_human_name = Sanitizer.as_identifier(metadata["singular"])
        schema_dict[table_human_name] = metadata
    with open(output, "w", encoding="utf-8") as file:
        if format == "python":
            tables = []
            file.write(f"from cmdapp.parser import {TableMeta.__name__}\n\n")
            for name, metadata in schema_dict.items():
                variable_name = f"table_{name}".upper()
                tables.append(variable_name)
                as_args = ", ".join(
                    f"{key}={repr(value)}" for key, value in metadata.items()
                )
                file.write(f"{variable_name} = {TableMeta.__name__}({as_args})\n\n")
            file.write(f"DATABASE_SCHEMA = [{', '.join(tables)}]\n")

        else:
            return json.dump(schema_dict, file, ensure_ascii=False, indent=2)
