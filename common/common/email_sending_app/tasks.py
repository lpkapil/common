from django.core.mail import send_mail
from django.conf import settings

def send_email(subject, message, recipient_list):
    """
    Send an email using Django's send_mail function.

    Args:
    - subject: The subject of the email.
    - message: The body of the email.
    - recipient_list: List of recipients (email addresses).
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
