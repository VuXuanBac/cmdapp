from datetime import date, datetime
import json
from enum import Enum


class Hash:
    def merge(d1: dict, d2: dict):
        """Merge two dict with strategy differ from operator `|`. The different is on same key:
        - d1 -> None ==> d2
        - d1 -> !None ==> d1

        Args:
            d1 (dict): The source dict (has higher priority)
            d2 (dict): The source dict

        Returns:
            dict: New dict merge items from both source dicts

        Examples:
        - Dict.merge({'a': 1, 'b': None, 'c': 3}, {'a': 10, 'b': '2', 'c': None}) ==> {'a': 1, 'b': '2', 'c': 3}
        - {'a': 1, 'b': None, 'c': 3} | {'a': 10, 'b': '2', 'c': None} ==> {'a': 10, 'b': '2', 'c': None}
        """
        result = {}
        for k in d1:
            result[k] = d1[k]
            if d1[k] is None and k in d2:
                result[k] = d2[k]
        return result | {k: v for k, v in d2.items() if k not in result}

    def filter(d: dict, *args, rename: dict[str, str] = {}) -> dict:
        """Filter items with keys in `args` and rename items with keys in `rename`

        Args:
            d (dict): The source dict
            args (list[str]): Allowed keys
            rename (dict[str, str]): key = new_name

        Returns:
            dict: New dict with all items with keys in `args` and renamed keys in `rename`
        """
        return {rename.get(k, k): v for k, v in d.items() if k in args or k in rename}

    def ignore(d: dict, *args, rename: dict[str, str] = {}) -> dict:
        """Return items with keys not in `args` and rename items with keys in `rename`

        Args:
            d (dict): The source dict
            args (list[str]): Not allowed keys
            rename (dict[str, str]): key = new_name

        Returns:
            dict: New dict with all items with keys not in `args` and renamed keys in `rename`
        """
        return {rename.get(k, k): v for k, v in d.items() if k not in args}

    def remove(d: dict, *values) -> dict:
        """Remove all items that its value is in values

        Args:
            d (dict): Origin dict
            values: values to match

        Returns:
            dict: New dict without items contains matched values
        """
        return {k: v for k, v in d.items() if v not in values}

    def find(d: dict, k, default):
        return d[k] if k in d else default

    def get(d: dict, /, **kwargs) -> object | list:
        """Get value from key. Return default if the dict does not have that key

        Args:
            d (dict): The source dict
            kwargs: key = default

        Returns:
            object | list: Array of extracted objects
        """
        result = []
        for k, v in kwargs.items():
            result.append(d[k] if k in d else v)
        return result[0] if len(result) == 1 else (result or None)

    def get_as_dict(d: dict, *args, **kwargs) -> dict:
        """Filter items with keys in `args` and default value (for missing keys) provided by `kwargs`

        Args:
            d (dict): The source dict
            args: key to filter, add None value for missing key
            kwargs: key = default

        Returns:
            dict: New dict with the keys are from kwargs

        Examples:
        - Dict.get_as_dict({'a': 1, 'b': 2, 'c': 3}, 'a', 'e', d=10, b=5, a=4) ==> {'d': 10, 'b': 2, 'a': 1, 'e': None}
        """
        return {k: d.get(k) for k in args} | {
            key: d.get(key, default) for key, default in kwargs.items()
        }

    def dig(d: dict, *path: str, default=None):
        current = d
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current


class Array:
    def find(d: list | tuple | set, v, default):
        return v if v in d else default

    def unpack_one(items: list | tuple):
        return list(items)[0] if len(items) == 1 else list(items)

    def filter(items: list | tuple | set, *, match=None, not_match=None):
        if callable(match):
            return [item for item in items if match(item)]
        if callable(not_match):
            return [item for item in items if not not_match(item)]
        return items


class Json:
    def load(data: str | bytes, **kwargs):
        if isinstance(data, (str, bytes)):
            return json.loads(data, **kwargs)
        return json.load(data, **kwargs)

    def dump(data, **kwargs):
        return json.dumps(
            data,
            default=kwargs.pop("default", None) or Json.serializer,
            ensure_ascii=False,
            **kwargs,
        )

    def serializer(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.name
        if hasattr(obj, "to_json"):
            return obj.to_json()
        raise TypeError(
            f"object [{obj}] with type [{type(obj)}] is not support to serialize as json",
            "try define a `to_json` method for it",
        )
