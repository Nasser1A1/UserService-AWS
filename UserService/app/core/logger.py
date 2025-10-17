import logging
from logging.handlers import RotatingFileHandler
import os
import sys


class LoggingService:
    """
    LoggingService provides a reusable and configurable logging setup.
    - Creates a rotating file handler (5 MB, 5 backups)
    - Logs to both console and file
    - Formats logs for readability
    """

    def __init__(self, log_dir="logs", log_file="app.log", level=logging.INFO, name="app_logger"):
        self.log_dir = log_dir
        self.log_file = log_file
        self.level = level
        self.name = name
        self.logger = None
        self._initialize_logger()

    def _initialize_logger(self):
        """Initialize and configure the logger"""
        os.makedirs(self.log_dir, exist_ok=True)
        log_path = os.path.join(self.log_dir, self.log_file)

        # Formatting: [timestamp] LEVEL in module: message
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )

        # Console handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)

        # Rotating file handler
        file_handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=5)
        file_handler.setFormatter(formatter)

        # Get or create logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.level)

        # Avoid duplicate handlers if already initialized
        if not self.logger.handlers:
            self.logger.addHandler(stream_handler)
            self.logger.addHandler(file_handler)

    def get_logger(self):
        """Return the logger instance"""
        return self.logger

    def set_level(self, level):
        """Dynamically change log level"""
        self.logger.setLevel(level)


