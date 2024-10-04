from django.utils.timezone import now
from .log_manager import log_message

class LoggingMiddleware:
    """
    Middleware to log every incoming HTTP request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        log_message(f"Request received: {request.method} {request.path} at {now()}")
        
        # Call the next middleware or view
        response = self.get_response(request)

        log_message(f"Response status: {response.status_code}")
        return response
