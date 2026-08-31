from base import decompose


class Request:
    """
    User-level HTTP request.

    This represents what the caller wants to send.
    It is NOT the final wire-ready request.
    """

    def __init__(
        self,
        method,
        url,
        headers=None,
        auth=None,
    ):
        self.method = method.upper()
        self.url = url
        self.headers = dict(headers or {})
        self.auth = auth


class PreparedRequest:
    """
    Fully prepared request ready to be sent through a Connection.

    This is the boundary between request preparation and
    network communication.
    """

    def __init__(
        self,
        method,
        url,
        headers,
        body=None,
        auth=None,
    ):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        self.auth = auth

        self.parsed_url = decompose(url)

    @property
    def path(self):
        return self.parsed_url.path_qs


class SessionState:
    """
    Persistent non-cookie state belonging to a Session.
    """

    def __init__(
        self,
        headers=None,
        auth=None,
        defaults=None,
    ):
        self.headers = dict(headers or {})
        self.auth = auth
        self.defaults = dict(defaults or {})

    def clear(self):
        self.headers.clear()
        self.auth = None
        self.defaults.clear()


class SessionManager:
    """
    Builds PreparedRequest objects.

    SessionManager does NOT:
        - open connections
        - send requests
        - own cookies

    It only combines request/session/header/cookie state.
    """

    def __init__(
        self,
        header_manager,
        cookie_engine,
        state=None,
    ):
        self.header_manager = header_manager
        self.cookie_engine = cookie_engine
        self.state = state or SessionState()

    def prepare_request(self, request):
        """
        Convert Request -> PreparedRequest.
        """

        # Header precedence:
        #
        # manager < session < request
        headers = self.header_manager.merge_headers(
            session_headers=self.state.headers,
            request_headers=request.headers,
        )

        # CookieEngine is the sole owner of cookie state.
        cookie_header = self.cookie_engine.get_cookie_header(
            request.url
        )

        if cookie_header is not None:
            self._set_header_case_insensitive(
                headers,
                "Cookie",
                cookie_header,
            )

        # auth is intentionally accepted but unused.
        return PreparedRequest(
            method=request.method,
            url=request.url,
            headers=headers,
            body=self.state.defaults.get("body"),
            auth=request.auth,
        )

    @staticmethod
    def _set_header_case_insensitive(headers, name, value):
        """Set a header while avoiding duplicate case variants."""
        for existing_name in list(headers):
            if existing_name.lower() == name.lower():
                del headers[existing_name]

        headers[name] = value