from ..database import Database
from ..parser import COLUMN_ID


class Alias:
    """If in a GUI application, you can use ID to reference everything (because you can get full record anytime)
    But in an Command Line, users prefer using name to reference a record to using its ID
    So this class is like a cache storage to lookup record ID from its name
    - If you just need to resolve once or twice, better to lookup directly with Database query using `Alias.resolve_directly`
    - If not, you can save this Class instance into App Class and reference it in prototype methods
    - If you want the alias keep updates in realtime, with new data, you should initialize it directly inside prototype methods
    """

    def __init__(
        self,
        database: Database,
        scope: list[str | tuple[str]],
        *,
        key_name: str = "name",
        full_record: bool = False,
    ):
        """Create an alias dictionary and cache the query to further lookup. If you want to just lookup once or twice, better to use static method `Alias.resolve_directly`

        Args:
            database (Database):  Database to query
            scope (list[str  |  tuple[str]]): Tables' names to match the aliases, use a list of tuple like `(table_a, column_b)` to override the `column_name` for this table
            key_name (str, optional): Column name to match the `values`. Defaults to "name".
            full_record (bool, optional): True if want to return full record instead of just record ID. Defaults to False.
        """
        aliases = {}
        key_struct = []
        for sc in scope:
            if isinstance(sc, tuple):
                key_struct.append((sc[0], sc[1]))
            elif isinstance(sc, str):
                key_struct.append((sc, key_name))

        # Get all records and cache them to alias object
        for table_name, key_name in key_struct:
            all_records = database[table_name].query(
                columns=None if full_record else [COLUMN_ID, key_name]
            )
            for record in all_records:
                aliases[(table_name, record[key_name])] = (
                    record if full_record else record[COLUMN_ID]
                )
        self.aliases = aliases

    def __contains__(self, key: tuple[str, str]):
        return key in self.aliases

    def __getitem__(self, key: tuple[str, str]):
        return self.aliases.get(key, None)

    def resolve(self, scope: str, values: list[str]):
        if not values:
            return None
        as_array = True
        if not isinstance(values, (tuple, list)):
            values = [values]
            as_array = False
        result = []
        for item in values:
            if not item:
                result.append(None)
            elif isinstance(item, int) or item.isdigit():
                result.append(int(item))
            else:
                key = (scope, item)
                if key not in self.aliases:
                    raise ValueError(f"NOT FOUND alias `{item}` in scope `{scope}`")
                result.append(self.aliases[key])
        return result if as_array else (result[0] if result else None)

    def resolve_directly(
        database: Database,
        scope: str,
        values: list[str],
        *,
        key_name: str = "name",
        full_record: bool = False,
    ) -> dict:
        """Resolve values directly with Database query

        Args:
            database (Database): Database to query
            scope (str): Table to lookup
            values (list[str]): List of alias value to resolve
            key_name (str, optional): Column name to match the `values`. Defaults to "name".
            full_record (bool, optional): True if want to return full record instead of just record ID. Defaults to False.

        Returns:
            dict: Map each column value to matched data (record or ID)
        """
        return database[scope].translate(
            key_name, *(values or []), full_record=full_record
        )
