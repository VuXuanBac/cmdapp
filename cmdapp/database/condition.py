from .constants import SQLOperators

from ..parser import COLUMN_ID


def _quote(use_quote: bool, value: object) -> object:
    """Get value after quoting (''). All data types will be quoted except: (1) int, (2) float and (3) named argument like `:name`

    Args:
        use_quote (bool): True to quote to int, float and named argument also
        value: Value to quote

    Returns:
        object: Value after quoting
    """
    if isinstance(value, (int, float)):
        q = use_quote
    elif isinstance(value, str) and value.startswith(":"):
        q = use_quote
    else:
        q = True
    return f"'{value}'" if q else str(value)


class SQLCondition:
    def __init__(
        self, *condition, negative: bool = False, force_quote: bool = False
    ) -> None:
        """Initialize statement for SQL Condition

        Args:
            condition (tuple): tuple of 2 or 3 parts in condition: <COLUMN> <OPERATOR> <DATA>?
            negative (bool, optional): True to prepend NOT into Condition String. Defaults to False.
            force_quote (bool, optional): True to force quoting on all data value. Defaults to False.

        """
        self.raw = [(condition, negative, force_quote)]

    def AND(self, *condition, negative: bool = False, force_quote: bool = False):
        """Concat with previous statement by an AND operator

        Args:
            condition (tuple): tuple of 2 or 3 parts in condition: <COLUMN> <OPERATOR> <DATA>?
            negative (bool, optional): True to prepend NOT into Condition String. Defaults to False.
            force_quote (bool, optional): True to force quoting on all data value. Defaults to False.

        Returns:
            self
        """
        self.raw.extend(["AND", (condition, negative, force_quote)])
        return self

    def OR(self, *condition, negative: bool = False, force_quote: bool = False):
        """Concat with previous statement by an OR operator

        Args:
            condition (tuple): tuple of 2 or 3 parts in condition: <COLUMN> <OPERATOR> <DATA>?
            negative (bool, optional): True to prepend NOT into Condition String. Defaults to False.
            force_quote (bool, optional): True to force quoting on all data value. Defaults to False.

        Returns:
            self
        """
        self.raw.extend(["OR", (condition, negative, force_quote)])
        return self

    def AND_GROUP(self, sql_condition: "SQLCondition"):
        self.raw.extend(["AND", "("] + sql_condition.raw + [")"])
        return self

    def OR_GROUP(self, sql_condition: "SQLCondition"):
        self.raw.extend(["OR", "("] + sql_condition.raw + [")"])
        return self

    def build(self) -> str:
        """Make SQL Condition string concat all statements

        Returns:
            str: SQL Condition string
        """
        processed = [
            v if isinstance(v, str) else SQLCondition.convert_to_string(*v)
            for v in self.raw
        ]
        return " ".join(processed)

    @staticmethod
    def with_id(value=None) -> "SQLCondition":
        """Create a SQL Condition for matching ID column

        Args:
            value (object, optional): ID value to match. If None, use a named argument. Defaults to None.

        Returns:
            SQLCondition: An SQL Condition to match ID
        """
        return SQLCondition(
            COLUMN_ID,
            SQLOperators.EQUAL,
            f":{COLUMN_ID}" if value is None else value,
            force_quote=False,
        )

    @staticmethod
    def convert_to_string(
        condition, negative: bool = False, force_quote: bool = False
    ) -> str:
        """Convert to Condition String

        Args:
            condition (tuple): tuple of 3 parts in condition: <COLUMN> <OPERATOR> <DATA>
            negative (bool, optional): True to prepend NOT into Condition String. Defaults to False.
            force_quote (bool, optional): True to force quoting on all data value. Defaults to False.

        Raises:
            ValueError: Condition tuple is invalid: Missing parts, Invalid DATA

        Returns:
            str: Condition String
        """
        try:
            # Process a single condition
            column, operator, value = (list(condition) + [None])[:3]

            if operator == SQLOperators.IN:
                formatted_values = ", ".join(_quote(force_quote, v) for v in value)
                base = f"{column} {operator} ({formatted_values})"
            elif operator == SQLOperators.LIKE:
                base = f"{column} {operator} {_quote(force_quote, value)}"
            elif operator == SQLOperators.BETWEEN:
                low, high = _quote(force_quote, value[0]), _quote(force_quote, value[1])
                base = f"{column} {operator} {low} AND {high}"
            elif (
                operator == SQLOperators.IS_NULL or operator == SQLOperators.IS_NOT_NULL
            ):
                base = f"{column} {operator}"
            else:
                base = f"{column} {operator} {_quote(force_quote, value)}"
            return ("NOT " if negative else "") + base
        except:
            raise ValueError(
                f"syntax for SQL condition is invalid: [{condition}]",
                "expect [column] [operator] [value]?, where [value] shoud be [None, int, str, list], depends on the [operator]",
            )

    def __str__(self):
        return self.build()
