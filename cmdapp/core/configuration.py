import json
import yaml
import re
from pathlib import Path


class Configuration:
    def load(path: str | Path):
        extension = Path(path).suffix
        try:
            with open(path, "r") as file:
                if extension == ".json":
                    return json.load(file)
                elif extension in [".yaml", ".yml"]:
                    return yaml.safe_load(file)
                else:
                    result = {}
                    pattern = r"^(\w[\w\d_.]*)\s*=\s*(.*)$"
                    for line in file:
                        match = re.match(pattern, line.strip())
                        if match:
                            key = match.group(1)
                            value = match.group(2)
                            result[key.upper()] = value
                    return result
        except:
            return {}
