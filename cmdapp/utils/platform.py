import shutil
from cmd2.ansi import style_aware_wcswidth, widest_line
import subprocess
import platform
import os


class Terminal:
    def width():
        return shutil.get_terminal_size().columns

    def height():
        return shutil.get_terminal_size().lines

    def count_display_chars(text: str, tab_size: int = 4):
        if isinstance(tab_size, int):
            text = text.replace("\t", " " * tab_size)
        single_line_count = style_aware_wcswidth(text)
        if single_line_count == -1:
            return widest_line(text)
        return single_line_count


class Platform:
    system = platform.system()
    abs = os.path.abspath
    isfile = os.path.isfile
    isdir = os.path.isdir

    def open_file(*arguments):
        args = list(arguments)
        os_type = Platform.system
        if os_type == "Windows":
            subprocess.run(["start"] + args, shell=True)
        elif os_type == "Darwin":  # macOS
            subprocess.run(["open"] + args)
        elif os_type == "Linux":
            subprocess.run(["xdg-open"] + args)

    def get_env():
        return os.environ.copy()

    def add_env(**kwargs):
        return os.environ.copy() | kwargs

    def set_path(*path: str):
        paths = os.pathsep.join(path)
        os.environ["PATH"] += f"{os.pathsep}{paths}"

    def cwd(file_name: str = ""):
        return os.path.join(os.getcwd(), file_name) if file_name else os.getcwd()

    def relpath(path, current_file):
        current_dir = os.path.dirname(current_file)
        return os.path.normpath(os.path.join(current_dir, path))

    def split_path(path):
        if not os.path.exists(path):
            return None, None
        if os.path.isfile(path):
            directory_path = os.path.dirname(path)
            file_name = os.path.basename(path)
            return directory_path, file_name
        return path, None

    def filename_without_extension(filename):
        return os.path.splitext(filename)[0]
