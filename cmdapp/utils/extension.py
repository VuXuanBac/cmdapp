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

    def filter(d: dict, *keys, **kwargs) -> dict:
        """Return new dict that contains all items from `kwargs` and items from `d` that has key in `keys`
        - Items with key in `keys` has higher priority than `kwargs`, on same key.
        Think of it as: Filter keys from source and merge with new dict for unset keys

        Args:
            d (dict): The source dict
            keys: Key to extract from the source dict
            kwargs: key = default. Default value for key that not in the source dict

        Returns:
            dict: New dict with all items from the source and the `kwargs` with the key in `keys` or `kwargs`

        Examples:
        - Dict.filter({'a': 1, 'b': 2, 'c': 3}, 'a', 'e', d=10, b=5, a=4) ==> {'d': 10, 'b': 5, 'a': 1}
        """
        return kwargs | {k: v for k, v in d.items() if k in keys}

    def ignore(d: dict, *args, **kwargs) -> dict:
        """Return new dict that contains all items from a dict that the key NOT in `args`

        Args:
            d (dict): The source dict
            args: The key to ignore
            kwargs (dict[str, str]): Keys to rename

        Returns:
            dict: New dict with all items from the source but the key not in `args`
        """
        return {kwargs.get(k, k): v for k, v in d.items() if k not in args}

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

    def get_as_dict(d: dict, **kwargs) -> dict:
        """Get value from key. Return default if the dict does not have that key.

        Args:
            d (dict): The source dict
            kwargs: key = default

        Returns:
            dict: New dict with the keys are from kwargs
        """
        return {key: d.get(key, default) for key, default in kwargs.items()}

    def dig(d: dict, *path: str, default=None):
        current = d
        for key in path:
            if key in current:
                current = current[key]
            else:
                return default
        return current


class Array:
    def find(d: dict, v, default):
        return v if v in d else default

    def unpack_one(items: list | tuple):
        if hasattr(items, "__len__"):
            return list(items)[0] if len(items) == 1 else list(items)
        return items


class Json:
    def load(data: str | bytes, **kwargs):
        if isinstance(data, (str, bytes)):
            return json.loads(data, **kwargs)
        return json.load(data, **kwargs)

    def dump(data: str | bytes, **kwargs):
        return json.dumps(
            data, default=kwargs.pop("default", None) or Json.serializer, **kwargs
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
