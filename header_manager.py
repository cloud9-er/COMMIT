class HeaderManager:
    """
    Manages persistent/default headers and prepares the final
    headers for a request.

    Precedence:
        manager headers < session headers < request headers
    """

    def __init__(self, headers=None):
        self.headers = dict(headers or {
            "User-Agent": "MyScraperBot/1.0",
            "Accept": "text/html,application/xhtml+xml",
        })

    def add_headers(self, key, value):
        """Add or replace a persistent manager-level header."""
        self.headers[key] = value

    def remove_header(self, key):
        """Remove a manager-level header if present."""
        for existing_key in list(self.headers):
            if existing_key.lower() == key.lower():
                del self.headers[existing_key]

    @staticmethod
    def _merge(base, override):
        """
        Merge headers case-insensitively.

        Values in override take precedence over values in base.
        """
        result = dict(base)

        for key, value in override.items():
            for existing_key in list(result):
                if existing_key.lower() == key.lower():
                    del result[existing_key]

            result[key] = value

        return result

    def merge_headers(self, session_headers=None, request_headers=None):
        """
        Apply header precedence:

            manager < session < request
        """
        merged = self._merge({}, self.headers)
        merged = self._merge(merged, session_headers or {})
        merged = self._merge(merged, request_headers or {})

        return merged