import logging
import inspect
from django.utils.timezone import now
from django.utils.deprecation import MiddlewareMixin

class SimpleLoggingMiddleware(MiddlewareMixin):
    """
    A middleware to log incoming HTTP requests and outgoing HTTP responses with additional details
    such as app name, view, class, function, line number, and request/response data.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details before processing the request
        self.log_request_details(request)

        # Call the next middleware or view
        response = self.get_response(request)

        # Log response details after processing the request
        self.log_response_details(request, response)

        return response

    def log_request_details(self, request):

        """
        Logs details of the incoming request, including app name, view, class, function, and more.
        """
        # Prepare log details
        log_message = {
            "timestamp": self.get_formatted_timestamp(),
            "method": request.method,
            "url": request.build_absolute_uri(),
            # "headers": dict(request.headers),
            "remote_ip": request.META.get('REMOTE_ADDR', 'Unknown'),
            "request_params": request.GET.dict() if request.method == 'GET' else request.POST.dict(),
            "app_name": self.get_app_name(request),
            "view": self.get_view_name(request),
            "class_name": self.get_class_name(request),
            "function_name": self.get_function_name(request),
            "line_number": self.get_line_number(request),
            "user": request.user if request.user.is_authenticated else "Anonymous",
        }

        # Get logger
        logger = logging.getLogger('request_logger')
        logger.info(f"Request: {log_message}")

    def log_response_details(self, request, response):
        """
        Logs details of the outgoing response, including app name, view, class, function, and more.
        """
        # Prepare log details
        log_message = {
            "timestamp": self.get_formatted_timestamp(),
            # "status_code": response.status_code,
            "url": request.build_absolute_uri(),
            "method": request.method,
            # "headers": dict(request.headers),
            "user": request.user if request.user.is_authenticated else "Anonymous",
            "remote_ip": request.META.get('REMOTE_ADDR', 'Unknown'),
            # "response_content": response.content.decode('utf-8')[:200],  # Log a snippet of the response content
            "app_name": self.get_app_name(request),
            "view": self.get_view_name(request),
            "class_name": self.get_class_name(request),
            "function_name": self.get_function_name(request),
            "line_number": self.get_line_number(request),
        }

        # Get logger
        logger = logging.getLogger('request_logger')
        logger.info(f"Response: {log_message}")

    def get_view_name(self, request):
        """
        Returns the view name for the current request.
        """
        if hasattr(request, 'resolver_match') and request.resolver_match:
            return request.resolver_match.view_name
        return 'Unknown'

    def get_app_name(self, request):
        """
        Returns the Django app name where the view is defined based on the view function/module.
        """
        # Check if the request has a valid resolver match
        if hasattr(request, 'resolver_match') and request.resolver_match:
            view_func = request.resolver_match.func  # Get the view function or class

            # If the view is a class-based view, we need to get the actual view class
            if hasattr(view_func, 'view_class'):
                view_func = view_func.view_class

            # Get the module path of the view
            module_path = inspect.getmodule(view_func).__name__

            # The app name will be the second-to-last part of the module path
            # e.g., 'myapp.views' -> 'myapp'
            if module_path:
                app_name = module_path.split('.')[0]  # Extract the app name from the module path
                return app_name
        
        return 'Unknown'

    def get_class_name(self, request):
        """
        Extracts the class name (if available) where the log message was generated.
        """
        # If the view is a class-based view, we can look up the view class
        if hasattr(request, 'resolver_match') and request.resolver_match:
            view = request.resolver_match.func
            if hasattr(view, 'view_class'):
                return view.view_class.__name__
            return 'Unknown'
        return 'Unknown'

    def get_function_name(self, request):
        """
        Extracts the function name of the view that is handling the request.
        """
        if hasattr(request, 'resolver_match') and request.resolver_match:
            view_func = request.resolver_match.func  # Get the view function or class

            # If the view is class-based, get the method (like 'get', 'post', etc.)
            if hasattr(view_func, 'view_class'):
                view_func = view_func.view_class
                # In class-based views, we can capture the method (e.g., 'get', 'post')
                method_name = request.resolver_match.view_name.split('.')[-1]
                return f"{view_func.__name__}.{method_name}"
            else:
                # If it's function-based, return the function name
                return view_func.__name__
        return 'Unknown'

    def get_line_number(self, request):
        """
        Extracts the line number from where the view was executed.
        """
        if hasattr(request, 'resolver_match') and request.resolver_match:
            view_func = request.resolver_match.func  # Get the view function or class

            if isinstance(view_func, type):  # If it's a class-based view (CBV)
                # The view function could be a class; we need to find the method
                view_method_name = request.resolver_match.view_name.split('.')[-1]
                try:
                    # Get the method of the class based on the method name (like 'get', 'post', etc.)
                    method = getattr(view_func, view_method_name, None)
                    if method:
                        # Get the source lines for the method, not the class itself
                        lines, starting_line = inspect.getsourcelines(method)
                        logging.debug(f"Class method {method.__name__} is defined at line {starting_line}")
                        return starting_line
                    else:
                        return 'Unknown'
                except (TypeError, OSError) as e:
                    logging.error(f"Error fetching class method source: {e}")
                    return 'Unknown'

            else:
                # If it's function-based view
                try:
                    # Use inspect to get the source lines of the function
                    lines, starting_line = inspect.getsourcelines(view_func)
                    logging.debug(f"Function {view_func.__name__} is defined at line {starting_line}")
                    return starting_line
                except (TypeError, OSError) as e:
                    logging.error(f"Error fetching function source: {e}")
                    return 'Unknown'
    
        return 'Unknown'

    def get_formatted_timestamp(self):
        """
        Returns the formatted timestamp string of the current time, including timezone if necessary.
        """
        # Get the current time and format it
        return now().strftime('%Y-%m-%d %H:%M:%S %Z')  # Example: 2024-10-04 07:19:00 UTC
