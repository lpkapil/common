from django.utils.timezone import now
from django.urls import resolve
from .log_manager import LoggerConfig

class LoggingMiddleware:
    """
    Middleware to log every incoming HTTP request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Auto-detect the app name
        app_name = self.get_app_name(request)

        # Create logger instance dynamically based on the app name
        logger = LoggerConfig(app_name)

        # Log the request
        logger.log_message(f"Request received: {request.method} {request.path} at {now()}")

        # Call the next middleware or view
        response = self.get_response(request)

        # Log the response status
        logger.log_message(f"Response status: {response.status_code}")

        return response

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
        # Assuming the module structure is like 'app_name.views.some_view'
        if len(module_name) > 1:
            return module_name[0]  # The first part is typically the app name
        
        # If we cannot extract the app name, fallback to 'unknown'
        return 'unknown'
