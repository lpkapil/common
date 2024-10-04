import logging
from django.utils.timezone import now
from django.urls import resolve
from django.db import connection
from django.http import HttpResponseServerError
from .log_manager import LoggerConfig  # Import the LoggerConfig class

class LoggingMiddleware:
    """
    Middleware to log every incoming HTTP request, database queries, and errors.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Auto-detect the app name
        app_name = self.get_app_name(request)

        # Create logger instance dynamically based on the app name
        logger = LoggerConfig(app_name)

        # Get current user and URL
        user = request.user if request.user.is_authenticated else 'Anonymous'
        url = request.get_full_path()
        view = resolve(request.path).view_name

        # Log the incoming request as an API call
        logger.log_message(
            f"Request received: {request.method} {request.path} at {now()}",
            log_type="API",
            user=user,
            url=url,
            view=view
        )

        # Capture and log database queries executed during the request
        self.log_database_queries(logger)

        # Call the next middleware or view
        try:
            response = self.get_response(request)

            # Log the response status
            logger.log_message(
                f"Response status: {response.status_code}",
                log_type="API",
                user=user,
                url=url,
                view=view
            )

        except Exception as e:
            # Log any unhandled exceptions as errors
            logger.log_message(
                f"Error occurred: {str(e)}",
                log_type="ERROR",
                user=user,
                url=url,
                view=view
            )
            # Raise the exception again so it can be handled by Django's default error handling
            raise e

        return response

    def log_database_queries(self, logger):
        """
        Log database queries if any are executed during the request.
        """
        if connection.queries:
            for query in connection.queries:
                logger.log_message(
                    f"Database Query: {query['sql']}, Time: {query['time']}",
                    log_type="DATABASE"
                )

    def get_app_name(self, request):
        """
        Extract the app name from the current view being processed.
        Uses the view function's module as a proxy for the app name.
        """
        # Get the view name (i.e., module or function)
        view_func = resolve(request.path).func
        
        # Extract the module or app name
        module_name = view_func.__module__.split('.')
        
        # If the module is in a specific app, use the app name
        if len(module_name) > 1:
            return module_name[0]  # The first part is typically the app name
        
        # If we cannot extract the app name, fallback to 'unknown'
        return 'unknown'
