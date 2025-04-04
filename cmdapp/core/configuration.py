import json
import yaml
import re
from pathlib import Path
from ..utils import Hash, Sanitizer

CONFIG_ENTRY_PATTERN = r"^([a-zA-Z][\w\.]*)\s*=\s*(.*)$"


class Configuration:
    @staticmethod
    def sanitize_config(configs: dict):
        return {
            Sanitizer.as_identifier(k).lower(): (
                Configuration.sanitize_config(v) if isinstance(v, dict) else v
            )
            for k, v in configs.items()
        }

    def __init__(self, path: str, default: dict = None):
        raw_data = default or {}
        if path:
            self.path = path
            raw_data |= Configuration.load(path)
        self.data = Configuration.sanitize_config(raw_data)

    def __contains__(self, key):
        return key.lower() in self.data

    def __str__(self):
        return str(self.data)

    def get(self, *keys, default=None):
        return Hash.dig(self.data, *[str(k).lower() for k in keys], default=default)

    def set(self, key, value):
        self.data[Sanitizer.as_identifier(key).lower()] = value
        return value

    def load(path: str | Path):
        extension = Path(path).suffix
        try:
            with open(path, "r", encoding="utf-8") as file:
                if extension == ".json":
                    return json.load(file)
                elif extension in [".yaml", ".yml"]:
                    return yaml.safe_load(file)
                else:
                    result = {}
                    for line in file:
                        match = re.match(CONFIG_ENTRY_PATTERN, line.strip())
                        if not match:
                            continue
                        # support two levels
                        keys = match.group(1).split(".", 1)
                        value = match.group(2)
                        if len(keys) > 1:
                            temp = result.setdefault(keys[0], {})
                            temp[keys[1]] = value
                        else:
                            result[keys[0]] = value
                        # temp = result
                        # for key in keys[:-1]:
                        #     temp = temp.setdefault(key)
                        # result[keys[-1]] = value
                    return result
        except:
            return {}

    def save(self, path: str | Path = None):
        path = self.path or path
        extension = Path(path).suffix
        try:
            with open(path, "w", encoding="utf-8") as file:
                if extension == ".json":
                    return json.dump(self.data, file, ensure_ascii=False)
                elif extension in [".yaml", ".yml"]:
                    return yaml.dump(self.data, file, allow_unicode=True)
                else:
                    lines = [f"{key} = {value}\n" for key, value in self.data.items()]
                    file.writelines(lines)
            return True
        except:
            return False
