from base import decompose

from connection_manager import HTTPConnectionManager
from cookie_engine import CookieEngine
from header_manager import HeaderManager
from session_manager import (
    Request,
    SessionManager,
    SessionState,
)


class Session:
    """
    High-level HTTP session.

    Session is the orchestrator.

    Responsibilities:
        1. Build Request.
        2. Ask SessionManager for PreparedRequest.
        3. Ask ConnectionManager for a connection.
        4. Send PreparedRequest through Connection.
        5. Give response to CookieEngine.
        6. Release connection back to ConnectionManager.
    """

    def __init__(
        self,
        connection_manager=None,
        state=None,
        header_manager=None,
        cookie_engine=None,
        session_manager=None,
    ):
        self.connection_manager = (
            connection_manager
            or HTTPConnectionManager()
        )

        self.state = state or SessionState()

        self.header_manager = (
            header_manager
            or HeaderManager()
        )

        self.cookie_engine = (
            cookie_engine
            or CookieEngine()
        )

        self.session_manager = (
            session_manager
            or SessionManager(
                header_manager=self.header_manager,
                cookie_engine=self.cookie_engine,
                state=self.state,
            )
        )

        self.closed = False

    def request(
        self,
        method,
        url,
        headers=None,
        auth=None,
        **kwargs,
    ):
        """
        Build and execute one HTTP request.

        auth is accepted but intentionally unused.
        """

        if self.closed:
            raise RuntimeError("Session is closed.")

        request = Request(
            method=method,
            url=url,
            headers=headers,
            auth=auth,
        )

        prepared_request = self.session_manager.prepare_request(
            request
        )

        parsed = decompose(prepared_request.url)

        # ConnectionManager owns all connections.
        pool, connection = self.connection_manager.acquire(parsed)

        try:
            response = connection.request(
                prepared_request.method,
                prepared_request.path,
                body=prepared_request.body,
                headers=prepared_request.headers,
            )

            # Session orchestrates cookie extraction.
            self.cookie_engine.extract_from_response(
                response,
                prepared_request.url,
            )

            return response

        except Exception:
            # Make sure a broken connection is not returned
            # as a reusable connection.
            if not connection.is_usable():
                pool.discard(connection)

            raise

        finally:
            if connection in pool.active:
                self.connection_manager.release(
                    pool,
                    connection,
                )

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
        Close the session's state.

        The ConnectionManager is not automatically closed because
        it may be shared by multiple sessions.
        """
        if self.closed:
            return

        self.state.clear()
        self.closed = True


if __name__ == "__main__":
    manager = HTTPConnectionManager(
        max_connections=3,
        max_connections_per_pool=1,
    )

    session = Session(
        connection_manager=manager
    )

    response = session.get(
        "https://www.bbc.com/"
    )

    print("Status:", response.status)
    print("Headers:", dict(response.getheaders()))

    response.read()

    session.close()
    manager.close()