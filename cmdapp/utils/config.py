import re


class Configuration:
    def load(path: str):
        try:
            with open(path, "r") as file:
                result = {}
                pattern = r"^(\w[\w\d_.]*)\s*=\s*(.*)$"
                for line in file:
                    match = re.match(pattern, line.strip())
                    if match:
                        key, value = match.groups()
                        result[key.upper()] = value
                return result
        except:
            return {}
