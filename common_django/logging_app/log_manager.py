import logging
import os
from django.conf import settings

class LoggerConfig:
    def __init__(self, app_name, log_dir=None, log_level=logging.DEBUG):
        """
        Initializes the logger configuration for the specified Django app.

        :param app_name: The name of the Django app or module.
        :param log_dir: Directory where log files should be stored. If None, defaults to BASE_DIR/logs.
        :param log_level: Logging level (e.g., DEBUG, INFO, ERROR, etc.). Defaults to DEBUG.
        """
        self.app_name = app_name
        self.log_dir = log_dir or os.path.join(settings.BASE_DIR, 'logs')
        self.log_level = log_level

        # Ensure the log directory exists
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Configure the logger
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(self.log_level)

        # Create a file handler
        log_file = os.path.join(self.log_dir, f"{self.app_name}_logs.log")
        file_handler = logging.FileHandler(log_file)
        
        # Create a formatter and attach it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

    def log_message(self, message):
        """
        Log a message using the configured logger.
        
        :param message: The message to be logged.
        """
        self.logger.info(message)


# Example of how to use it in a Django app:
# Create a logger instance for your app
my_logger = LoggerConfig('my_app')

# Log a message
my_logger.log_message('This is a log message from my_app.')
