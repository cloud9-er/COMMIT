from urllib.parse import urlsplit


class ParsedURL:
    """
    A decomposed URL. host/port are split apart
    """

    def __init__(self, scheme, host, port=None, path="", query="", fragment=""):
        self.scheme = scheme
        self.host = host
        self.port = port
        self.path = path
        self.query = query
        self.fragment = fragment

    @property
    def path_qs(self):
        """Path + query string, suitable as an HTTP request target."""
        target = self.path or "/"
        if self.query:
            target = f"{target}?{self.query}"
        return target


def decompose(url):
    parts = urlsplit(url)
    return ParsedURL(
        scheme=parts.scheme,
        host=parts.hostname,
        port=parts.port,
        path=parts.path,
        query=parts.query,
        fragment=parts.fragment,
    )
