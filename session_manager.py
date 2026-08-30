from http.cookies import SimpleCookie
from urllib.parse import urlparse


class SessionState:
    """
    Stores HTTP state that persists across requests.
    """

    def __init__(
        self,
        headers=None,
        cookies=None,
        auth=None,
        defaults=None,
    ):
        self.headers = dict(headers or {})
        self.cookies = dict(cookies or {})
        self.auth = auth
        self.defaults = dict(defaults or {})

    def prepare_request(self, request):
        """
        Apply persistent session state to a Request.
        """

        # Session headers provide defaults.
        for name, value in self.headers.items():
            if name not in request.headers:
                request.headers[name] = value

        # Session cookies provide defaults.
        for name, value in self.cookies.items():
            if name not in request.cookies:
                request.cookies[name] = value

        # Session authentication is used when the request
        # does not provide its own authentication.
        if request.auth is None:
            request.auth = self.auth

        # Apply other session-level defaults.
        for name, value in self.defaults.items():
            if not hasattr(request, name) or getattr(request, name) is None:
                setattr(request, name, value)

        return request

    def update_from_response(self, response):
        """
        Update persistent state using information from a Response.
        """

        set_cookie = response.headers.get("Set-Cookie")

        if set_cookie:
            cookie = SimpleCookie()
            cookie.load(set_cookie)

            for name, morsel in cookie.items():
                self.cookies[name] = morsel.value

    def clear(self):
        """Clear all persistent session state."""
        self.headers.clear()
        self.cookies.clear()
        self.auth = None
        self.defaults.clear()


class Session:
    """
    High-level HTTP session.
    """

    def __init__(self, connection_manager, state=None):
        self.connection_manager = connection_manager
        self.state = state or SessionState()

    def request(
        self,
        method,
        url,
        headers=None,
        cookies=None,
        auth=None,
        **kwargs,
    ):
        """
        Execute one HTTP request using persistent session state.
        """

        # Request is assumed to be an existing project component.
        request = Request(
            method=method,
            url=url,
            headers=headers or {},
            cookies=cookies or {},
            auth=auth,
            **kwargs,
        )

        # Apply persistent state.
        request = self.state.prepare_request(request)

        # Determine the connection key.
        parsed = urlparse(url)

        connection_key = (
            parsed.scheme,
            parsed.hostname,
            parsed.port or self._default_port(parsed.scheme),
        )

        # Ask the connection manager for a connection.
        connection = self.connection_manager.acquire(connection_key)

        try:
            # Connection is a black-box object.
            response = connection.send(request)

            # Let SessionState inspect the response.
            self.state.update_from_response(response)

            return response

        finally:
            # Always return the connection to the manager.
            self.connection_manager.release(connection)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def close(self):
        """
        Session itself does not own the connection manager,
        so closing the session does not necessarily mean closing
        shared connection infrastructure.
        """

        self.state.clear()

    @staticmethod
    def _default_port(scheme):
        if scheme == "http":
            return 80

        if scheme == "https":
            return 443

        raise ValueError(f"Unsupported scheme: {scheme}")