import time
import random
import socket


class RetryEngine():
    def __init__(self, max_retries = 3, backoff_factor = 0.5, sleep_function = time.sleep):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.sleep_function = sleep_function

    def status_to_retry(self, status):
        """Decide whether an HTTP response should be retried."""

        """429 Too Many Requests
        500 Internal Server Error
        502 Bad Gateway
        503 Service Unavailable
        504 Gateway Timeout"""

        return status == 429 or status in (500, 502, 503, 504)


    def exception_to_retry(self, exception):
        """Decide whether a network exception should be retried."""

        return isinstance(exception, 
                          (
                              socket.timeout,
                              ConnectionResetError,
                              ConnectionAbortedError,
                              BrokenPipeError
                              )
                              )


    def get_backoff_time(self, attempt):
        delay = self.backoff_factor * (2 ** attempt)
        jitter = random.uniform(0, 0.1)

        return delay + jitter


    def get_retry_after(self, response):
        retry_after = response.headers.get("Retry-After")

        if retry_after is None:
            return None

        try:
            return float(retry_after)

        except (TypeError, ValueError):
            return None

        
    
    def execute(self, connection_manager, url, method, path, body = None, headers = None):

        for attempt in range(self.max_retries + 1):

            pool = None
            connection = None

            try:

                pool, connection = connection_manager.acquire(url)

                response = connection.request(method, path, body = body, headers = headers)

                if not self.status_to_retry(response.status):
                    return response

                if attempt == self.max_retries:
                    return response


                retry_after = self.get_retry_after(response)

                if retry_after is not None:
                    delay = retry_after
                else:
                    delay = self.get_backoff_time(attempt)

                self.sleep_function(delay)


            except Exception as exception:

                if not self.exception_to_retry(exception):
                    raise
                
                if attempt == self.max_retries:
                    raise

                delay = self.get_backoff_time(attempt)
                self.sleep_function(delay)

            finally:
                if pool is not None and connection is not None:
                    connection_manager.release(pool, connection)
