import logging
import os
import inspect
from django.conf import settings

class LoggerConfig:
    """
    Configures logging for the Django application.
    Logs messages with additional context, such as the user, app name,
    location, log type, URL, view, module, class, function.
    """

    def __init__(self, app_name, log_dir=None):
        """
        Initializes the logger configuration for the specified Django app.

        :param app_name: The name of the Django app or module.
        :param log_dir: Directory where log files should be stored. Defaults to BASE_DIR/logs.
        """
        self.app_name = app_name
        self.log_dir = log_dir or os.path.join(settings.BASE_DIR, 'logs')

        # Set the log level from the app-specific config or use the default level
        self.log_level = self.get_log_level(app_name)

        # Ensure the log directory exists
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Configure the logger
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(self.log_level)

        # Create a file handler
        log_file = os.path.join(self.log_dir, f"{self.app_name}_logs.log")
        file_handler = logging.FileHandler(log_file)
        
        # Create a formatter with additional log details (user, app_name, location, etc.)
        formatter = self.create_formatter()

        # Set the formatter for the file handler
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

    def get_log_level(self, app_name):
        """
        Get the log level for the given app, defaulting to 'WARNING' if not specified.
        """
        # Use the custom setting MY_LOGGING_CONFIG to get the log level for the app
        log_config = getattr(settings, 'MY_LOGGING_CONFIG', {})
        # Use app-specific log level if defined, otherwise fallback to 'default'
        return log_config.get(app_name, log_config.get('default', 'WARNING'))

    def create_formatter(self):
        """
        Create a log formatter that includes:
        - Current user
        - App name
        - File location
        - Log type (e.g., API, Error, DB)
        - URL
        - View
        - Module, class, function name
        """
        log_format = (
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - '
            'User: %(user)s - App: %(app_name)s - Location: %(pathname)s:%(lineno)d - '
            'Log Type: %(log_type)s - URL: %(url)s - View: %(view)s - '
            'Module: %(module)s - Function: %(funcName)s - Class: %(className)s'
        )
        return logging.Formatter(log_format)

    def log_message(self, message, log_type='INFO', user=None, url=None, view=None):
        """
        Log a message using the configured logger with additional context.

        :param message: The message to be logged.
        :param log_type: The type of log (e.g., API, Database, Error).
        :param user: The user performing the action (if available).
        :param url: The URL being accessed (if applicable).
        :param view: The view being processed (if applicable).
        """
        extra_context = {
            'user': user or 'Anonymous',
            'app_name': self.app_name,
            'log_type': log_type,
            'url': url or 'N/A',
            'view': view or 'N/A',
            'className': inspect.stack()[1].frame.f_globals.get('__name__', 'N/A'),
            'funcName': inspect.currentframe().f_code.co_name,
        }

        # Avoid overwriting fields like 'module', 'pathname', and 'lineno'
        if 'module' in extra_context:
            del extra_context['module']
        if 'pathname' in extra_context:
            del extra_context['pathname']
        if 'lineno' in extra_context:
            del extra_context['lineno']

        # Use the appropriate log level
        if log_type == 'ERROR':
            self.logger.error(message, extra=extra_context)
        elif log_type == 'DEBUG':
            self.logger.debug(message, extra=extra_context)
        elif log_type == 'WARNING':
            self.logger.warning(message, extra=extra_context)
        elif log_type == 'DATABASE':
            self.logger.debug(message, extra=extra_context)
        else:
            self.logger.info(message, extra=extra_context)
