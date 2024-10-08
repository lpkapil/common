from django.apps import AppConfig
from django.core.signals import setting_changed
from django.dispatch import receiver
import threading, schedule

class LoggingAppConfig(AppConfig):
    name = 'common_django.logging_app'
    verbose_name = 'Logging App'

    def ready(self):
        from common_django.logging_app.schedular import LogScheduler
        from django.conf import settings
        """
        Start the log scheduler and listen for setting changes.
        """
        # Start the scheduler initially with current settings
        self.start_scheduler(LogScheduler, settings)

        # Connect the signal to handle setting changes
        setting_changed.connect(self.reload_scheduler_on_change)

    def start_scheduler(self, LogScheduler, settings):
        """
        Start the log scheduler with the current settings.
        """
        frequency = getattr(settings, 'LOG_FREQUENCY', 'minutes')
        interval = getattr(settings, 'LOG_INTERVAL', 1)

        print('params', [frequency, interval])

        def start_scheduler():
            LogScheduler(frequency=frequency, interval=interval)

        scheduler_thread = threading.Thread(target=start_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()

    @receiver(setting_changed)
    def reload_scheduler_on_change(self, sender, setting, value, **kwargs):
        """
        Restart the log scheduler if LOG_FREQUENCY or LOG_INTERVAL is changed.
        """
        if setting == 'LOG_FREQUENCY' or setting == 'LOG_INTERVAL':
            # Clear current schedule
            schedule.clear()

            # Restart the scheduler with updated settings
            self.start_scheduler()
            print(f"Scheduler reinitialized due to change in {setting}: {value}")
