from django.db import models
from django.contrib.auth.models import User
import hashlib

class RequestLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10)
    url = models.URLField()
    remote_ip = models.GenericIPAddressField()
    request_params = models.JSONField(null=True, blank=True)
    app_name = models.CharField(max_length=255)
    view = models.CharField(max_length=255)
    class_name = models.CharField(max_length=255)
    function_name = models.CharField(max_length=255)
    line_number = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # A new field to store the hash of the log data
    log_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)  # SHA-256 hash

    def __str__(self):
        return f"{self.timestamp} - {self.method} - {self.url} - {self.user}"

    def save(self, *args, **kwargs):
        # Generate the hash before saving the entry
        if not self.log_hash:
            log_data_str = f"{self.timestamp}-{self.url}-{self.user}-{self.method}"  # Create a unique string
            self.log_hash = hashlib.sha256(log_data_str.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Request Log'
        verbose_name_plural = 'Request Logs'
        unique_together = ('timestamp', 'url', 'user')  # Unique constraint on the combination of these fields
