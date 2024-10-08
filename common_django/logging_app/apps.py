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
        
        # Initialize a threading event to control the scheduler thread
        self.scheduler_running = threading.Event()
        
        # Start or stop the scheduler based on LOG_ENABLED setting
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
            # Set the event to signal the scheduler thread to run
            self.scheduler_running.set()

            def start_scheduler():
                # Create an instance of LogScheduler
                log_scheduler_instance = self.LogScheduler(frequency=frequency, interval=interval)
                log_scheduler_instance.start()  # Start the scheduler

                # Schedule the job with a name
                job_name = 'log_processor_task'  # Define a unique name for the job
                schedule.every(interval).minutes.do(log_scheduler_instance.log_processor_task).tag(job_name)

                # Keep running while the event is set
                while self.scheduler_running.is_set():
                    schedule.run_pending()
                    time.sleep(1)  # Sleep to prevent busy waiting

            # Start the scheduler thread
            self.scheduler_thread = threading.Thread(target=start_scheduler)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
        else:
            # Stop logging if it's currently running
            self.stop_logging()

        print('All jobs:', schedule.get_jobs())

    def stop_logging(self):
        """
        Stop the log scheduler if it's running.
        """
        print("Stopping logging...")

        # Clear the running flag to stop the scheduler thread
        self.scheduler_running.clear()
        
        # Instead of clearing all, identify and remove specific jobs by their tag
        for job in schedule.get_jobs():
            if job.tags and 'log_processor_task' in job.tags:  # Check for the job tag
                schedule.cancel_job(job)  # Cancels only the jobs related to logging
        
        # Print jobs to confirm they have been cleared
        print('All jobs after stopping:', schedule.get_jobs())

    @receiver(setting_changed)
    def reload_scheduler_on_change(self, sender, setting, value, **kwargs):
        """
        Restart the log scheduler if LOG_FREQUENCY, LOG_INTERVAL, or LOG_ENABLED is changed.
        """
        if setting in ['LOG_FREQUENCY', 'LOG_INTERVAL', 'LOG_ENABLED']:
            # Restart the scheduler based on updated LOG_ENABLED setting
            self.manage_scheduler()
            print(f"Scheduler reinitialized due to change in {setting}: {value}")
