from django.apps import AppConfig
from django.core.signals import setting_changed
from django.dispatch import receiver
import threading
import schedule
from django.conf import settings

class LoggingAppConfig(AppConfig):
    name = 'common_django.logging_app'
    verbose_name = 'Logging App'

    def ready(self):
        from common_django.logging_app.schedular import LogScheduler
        
        # Store LogScheduler in an instance variable
        self.LogScheduler = LogScheduler
        
        """
        Start or stop the scheduler based on LOG_ENABLED setting
        """
        self.manage_scheduler()

        # Connect the signal to handle setting changes
        setting_changed.connect(self.reload_scheduler_on_change)

    def manage_scheduler(self):
        """
        Start or stop the log scheduler based on the LOG_ENABLED setting.
        """
        log_enabled = getattr(settings, 'LOG_ENABLED', False)
        frequency = getattr(settings, 'LOG_FREQUENCY', 'minutes')
        interval = getattr(settings, 'LOG_INTERVAL', 1)

        print(f'Logging params - LOG_ENABLED: {log_enabled}, LOG_FREQUENCY: {frequency}, LOG_INTERVAL: {interval}')

        if log_enabled:
            
            def start_scheduler():
                log_scheduler_instance = self.LogScheduler(frequency=frequency, interval=interval)
                log_scheduler_instance.start()  # Start the scheduler

            # Start the scheduler thread
            self.scheduler_thread = threading.Thread(target=start_scheduler)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
        else:
            # Stop logging if it's currently running
            self.stop_logging()

    def stop_logging(self):
        """
        Stop the log scheduler if it's running.
        """
        print("Stopping logging...")

        # Clear the current schedule
        schedule.clear()

    @receiver(setting_changed)
    def reload_scheduler_on_change(self, sender, setting, value, **kwargs):
        """
        Restart the log scheduler if LOG_FREQUENCY, LOG_INTERVAL or LOG_ENABLED is changed.
        """
        if setting in ['LOG_FREQUENCY', 'LOG_INTERVAL', 'LOG_ENABLED']:
            # Restart the scheduler based on updated LOG_ENABLED setting
            self.manage_scheduler(sender)
            print(f"Scheduler reinitialized due to change in {setting}: {value}")

