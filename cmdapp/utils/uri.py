from pathlib import Path
import urllib.parse as uri
import platform


class URI:
    join = uri.urljoin

    def to_uri(path):
        return Path(path).resolve().as_uri()

    def resolve(link):
        parsed = uri.urlparse(link)
        if parsed.scheme in ("http", "https", "ftp", "ftps", "sftp"):
            return link, True
        elif parsed.scheme == "file":
            file_path = uri.unquote(parsed.path)
            # For Windows paths, remove leading '/': 'file:///C:/path/to/file'
            if platform.system() == "Windows" and file_path.startswith(("/", "\\")):
                file_path = file_path[1:]
        else:
            file_path = link

        path = Path(file_path)
        if path.exists() and path.is_file():
            return file_path, False
        return None, None

    def is_remote(link: str):
        parsed = uri.urlparse(link)
        return parsed.scheme in ("http", "https", "ftp", "ftps", "sftp")
