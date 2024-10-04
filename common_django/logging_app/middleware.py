import logging
from django.utils.timezone import now
from django.utils.deprecation import MiddlewareMixin

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log details of incoming requests.
    """

    def process_request(self, request):
        """
        Logs user, request path, URL, headers, request params, and other necessary details.
        """
        # Prepare the log message with necessary details
        log_details = {
            'timestamp': now(),
            'user': request.user if request.user.is_authenticated else 'Anonymous',
            'url': request.build_absolute_uri(),
            'method': request.method,
            'view': self.get_view_name(request),
            'app_name': self.get_app_name(request),
            'request_params': request.GET.dict() if request.method == 'GET' else request.POST.dict(),
            'headers': dict(request.headers),
            'remote_ip': request.META.get('REMOTE_ADDR', ''),
        }

        # Log the details
        logger = logging.getLogger('request_logger')
        logger.info(log_details)

    def get_view_name(self, request):
        """
        Returns the view name for the current request.
        """
        if hasattr(request, 'resolver_match') and request.resolver_match:
            return request.resolver_match.view_name
        return 'Unknown View'

    def get_app_name(self, request):
        """
        Return the app name based on the current request URL.
        """
        app_name = request.path.split('/')[1] if request.path else 'Unknown App'
        return app_name
