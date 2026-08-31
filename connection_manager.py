import socket

import http.client
import ssl
import threading
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

@dataclass(frozen=True)
class ConnectionKey:
    scheme: str
    host: str
    port: int

class ConnectionState(Enum):
    NEW = auto()
    CONNECTING = auto()
    IDLE = auto()
    ACTIVE = auto()
    FAILED = auto()
    CLOSED = auto()

class Connection:
    def __init__(
        self,
        key: ConnectionKey,
        ssl_context: ssl.SSLContext,
        timeout: float | None = 10.0,
    ):
        self.key = key
        self.timeout = timeout

        self.state = ConnectionState.NEW

        self.created_at = time.monotonic()
        self.last_used_at = self.created_at

        self._http_connection = None

        self._ssl_context = ssl_context

    def connect(self):
        if self.state == ConnectionState.CLOSED:
            raise RuntimeError("Cannot connect a closed connection.")

        self.state = ConnectionState.CONNECTING

        try:
            if self.key.scheme == "https":
                self._http_connection = http.client.HTTPSConnection(
                    self.key.host,
                    self.key.port,
                    timeout=self.timeout,
                    context=self._ssl_context,
                )
            else:
                self._http_connection = http.client.HTTPConnection(
                    self.key.host,
                    self.key.port,
                    timeout=self.timeout,
                )

            self._http_connection.connect()

            self.state = ConnectionState.IDLE
            self.last_used_at = time.monotonic()

        #added for timeout
        except socket.timeout:
            self.state = ConnectionState.FAILED
            self.close()
            raise

        
        except Exception:
            self.state = ConnectionState.FAILED
            self.close()
            raise

    def is_usable(self):
        return (
            self.state in
            (ConnectionState.IDLE, ConnectionState.ACTIVE)
            and self._http_connection is not None
        )

    def request(self, method, path, body=None, headers=None):
        if not self.is_usable():
            raise RuntimeError("Connection is not usable.")

        self.state = ConnectionState.ACTIVE
        self.last_used_at = time.monotonic()

        try:
            self._http_connection.request(
                method,
                path,
                body=body,
                headers=headers or {},
            )

            response = self._http_connection.getresponse()

            self.last_used_at = time.monotonic()

            return response

        #added timeout exception handling
        except socket.timeout:
            self.state = ConnectionState.FAILED
            self.close()
            raise

        except Exception:
            self.state = ConnectionState.FAILED
            raise

    def release(self):
        if self.state == ConnectionState.ACTIVE:
            self.state = ConnectionState.IDLE
            self.last_used_at = time.monotonic()

    def close(self):
        if self._http_connection is not None:
            try:
                self._http_connection.close()
            except Exception:
                pass

        self.state = ConnectionState.CLOSED

    @property
    def age(self):
        return time.monotonic() - self.created_at

    @property
    def idle_time(self):
        return time.monotonic() - self.last_used_at

class ConnectionPool:
    def __init__(
        self,
        key: ConnectionKey,
        manager,
        max_connections: int = 5,
    ):
        self.key = key
        self.manager = manager
        self.max_connections = max_connections

        self.idle = deque()
        self.active = set()

        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

        self.closed = False

    @property
    def connection_count(self):
        return len(self.idle) + len(self.active)

    def acquire(self):
        with self.condition:

            if self.closed:
                raise RuntimeError("Connection pool is closed.")

            while True:

                # 1. Reuse an idle connection.
                while self.idle:
                    connection = self.idle.popleft()

                    if connection.is_usable():
                        connection.state = ConnectionState.ACTIVE
                        self.active.add(connection)
                        return connection

                    # Stale/broken connection.
                    connection.close()
                    self.manager._connection_closed(connection)

                # 2. Create a new connection if the pool allows it.
                if self.connection_count < self.max_connections:

                    # Reserve global capacity while holding the
                    # manager lock and then create the connection.
                    if self.manager._reserve_connection_slot():

                        connection = Connection(
                            self.key,
                            self.manager.ssl_context,
                            self.manager.timeout,
                        )

                        try:
                            connection.connect()

                        except Exception:
                            self.manager._connection_closed(connection)
                            raise

                        connection.state = ConnectionState.ACTIVE
                        self.active.add(connection)

                        return connection

                # 3. Pool/global capacity is exhausted.
                #
                # Wait until another thread releases a connection.
                self.condition.wait()

                if self.closed:
                    raise RuntimeError("Connection pool was closed.")

    def release(self, connection):

        with self.condition:

            if connection not in self.active:
                raise RuntimeError(
                    "Connection does not belong to the active pool."
                )

            self.active.remove(connection)

            if connection.state == ConnectionState.FAILED:
                connection.close()
                self.manager._connection_closed(connection)

            elif connection.is_usable():
                connection.release()
                self.idle.append(connection)

            else:
                connection.close()
                self.manager._connection_closed(connection)

            # Wake one waiting thread.
            self.condition.notify()

    def discard(self, connection):

        with self.condition:

            self.idle = deque(
                c for c in self.idle
                if c is not connection
            )

            self.active.discard(connection)

            connection.close()
            self.manager._connection_closed(connection)

            self.condition.notify()

    def close(self):

        with self.condition:

            self.closed = True

            connections = list(self.idle) + list(self.active)

            self.idle.clear()
            self.active.clear()

            for connection in connections:
                connection.close()
                self.manager._connection_closed(connection)

            # Wake threads that may be waiting in acquire().
            self.condition.notify_all()

class HTTPConnectionManager:

    def __init__(
        self,
        max_connections: int = 20,
        max_connections_per_pool: int = 5,
        timeout: float | None = 10.0,
        ssl_context: ssl.SSLContext | None = None,
    ):
        self.max_connections = max_connections
        self.max_connections_per_pool = max_connections_per_pool
        self.timeout = timeout

        # One persistent SSL context shared by HTTPS connections.
        self.ssl_context = (
            ssl_context
            if ssl_context is not None
            else ssl.create_default_context()
        )

        # Connection pools indexed by ConnectionKey.
        self.pools = {}

        # Global connection count.
        self.total_connections = 0

        # Protects global state.
        self.lock = threading.Lock()

        self.closed = False

    def _get_pool(self, key):

        with self.lock:

            if self.closed:
                raise RuntimeError(
                    "HTTPConnectionManager is closed."
                )

            pool = self.pools.get(key)

            if pool is None:
                pool = ConnectionPool(
                    key=key,
                    manager=self,
                    max_connections=self.max_connections_per_pool,
                )

                self.pools[key] = pool

            return pool

    def _reserve_connection_slot(self):

        with self.lock:

            if self.closed:
                return False

            if self.total_connections >= self.max_connections:
                return False

            self.total_connections += 1

            return True

    def _connection_closed(self, connection):

        with self.lock:

            if self.total_connections > 0:
                self.total_connections -= 1

    def acquire(self, parsed):
        """
        Get a (pool, connection) pair for the given ParsedURL.
        This is the only way a Connection should ever be obtained --
        callers never construct Connection objects themselves.
        """

        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                "Only HTTP and HTTPS are supported."
            )

        # Respect an explicit port from the URL; fall back to the
        # scheme's default only when none was given.
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        key = ConnectionKey(
            scheme=parsed.scheme,
            host=parsed.host,
            port=port,
        )

        pool = self._get_pool(key)

        return pool, pool.acquire()

    def release(self, pool, connection):

        pool.release(connection)

    def close(self):

        with self.lock:

            if self.closed:
                return

            self.closed = True

            pools = list(self.pools.values())

        for pool in pools:
            pool.close()

        with self.lock:
            self.pools.clear()
            self.total_connections = 0