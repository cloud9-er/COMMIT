import time
import random
import socket


class RetryEngine:
    def __init__(
        self,
        max_retries=3,
        backoff_factor=0.5,
        sleep_function=time.sleep,
        logger=None
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.sleep_function = sleep_function
        self.logger = logger

    def status_to_retry(self, status):
        """
        Decide whether an HTTP response should be retried.

        Retryable responses:
        429 Too Many Requests
        500 Internal Server Error
        502 Bad Gateway
        503 Service Unavailable
        504 Gateway Timeout
        """

        return status == 429 or status in (500, 502, 503, 504)

    def exception_to_retry(self, exception):
        """
        Decide whether a network exception should be retried.
        """

        return isinstance(
            exception,
            (
                socket.timeout,
                ConnectionResetError,
                ConnectionAbortedError,
                BrokenPipeError
            )
        )

    def get_backoff_time(self, attempt):
        """
        Calculate exponential backoff with small random jitter.
        """

        delay = self.backoff_factor * (2 ** attempt)
        jitter = random.uniform(0, 0.1)

        return delay + jitter

    def get_retry_after(self, response):
        """
        Read Retry-After from the response headers.
        """

        retry_after = response.headers.get("Retry-After")

        if retry_after is None:
            return None

        try:
            return float(retry_after)

        except (TypeError, ValueError):
            return None

    def execute(
        self,
        connection_manager,
        url,
        method,
        path,
        body=None,
        headers=None
    ):
        """
        Execute a request with retry handling.
        """

        for attempt in range(self.max_retries + 1):

            pool = None
            connection = None

            try:
                # Get a connection from T2.
                pool, connection = connection_manager.acquire(url)

                # Send the request through the T2 connection.
                response = connection.request(
                    method,
                    path,
                    body=body,
                    headers=headers
                )

                # Successful/non-retryable response.
                if not self.status_to_retry(response.status):
                    return response

                # No retries remaining.
                if attempt == self.max_retries:

                    if self.logger:
                        self.logger.error(
                            f"Maximum retries exceeded. "
                            f"Final HTTP status: {response.status}"
                        )

                    return response

                # Server may tell us how long to wait.
                retry_after = self.get_retry_after(response)

                if retry_after is not None:
                    delay = retry_after
                else:
                    delay = self.get_backoff_time(attempt)

                # record retry information.
                if self.logger:
                    self.logger.warning(
                        f"HTTP {response.status} received. "
                        f"Retrying attempt {attempt + 1}"
                    )

                    self.logger.info(
                        f"Waiting {delay:.2f} seconds before retry"
                    )

                # Wait before retrying.
                self.sleep_function(delay)

            except Exception as exception:

                # Not a retryable exception.
                if not self.exception_to_retry(exception):
                    raise

                # No retries remaining.
                if attempt == self.max_retries:

                    if self.logger:
                        self.logger.error(
                            f"Maximum retries exceeded. "
                            f"Final exception: {exception}"
                        )

                    raise

                # record retryable exception.
                if self.logger:
                    self.logger.warning(
                        f"Retryable exception: {exception}"
                    )

                # Calculate backoff.
                delay = self.get_backoff_time(attempt)

                # record backoff.
                if self.logger:
                    self.logger.info(
                        f"Waiting {delay:.2f} seconds before retry"
                    )

                # Wait before retrying.
                self.sleep_function(delay)

            finally:

                # Always return the connection to T2.
                if pool is not None and connection is not None:
                    connection_manager.release(
                        pool,
                        connection
                    )