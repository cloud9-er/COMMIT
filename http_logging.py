import logging


class HTTPLogger:
    def __init__(self):
        """For recording INFO and more serious messages."""
        self.logger = logging.getLogger("http_client")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            """This sends the logs to the terminal"""
            handler = logging.StreamHandler()

            """Give the logs their required structure"""
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )

            handler.setFormatter(formatter)
            self.logger.addHandler(handler)


    def info(self, message):
        self.logger.info(message)


    def warning(self, message):
        self.logger.warning(message)


    def error(self, message):
        self.logger.error(message)


    def debug(self, message):
        self.logger.debug(message)


