import os
import django
import sys
import schedule
import time
import logging
from common_django.logging_app.log_processor import LogProcessor  # Import your class-based log processor

# Set up logger
logger = logging.getLogger('log_scheduler')

class LogScheduler:
    def __init__(self, frequency, job_time=None, interval=None, timezone=None):
        """
        Initialize the LogScheduler with specified scheduling conditions.

        :param frequency: Frequency of the scheduling ('seconds', 'minutes', 'hour', 'daily', 'weekly').
        :param job_time: Specific time to run the job (e.g., "10:30" for daily).
        :param interval: Interval for scheduling (e.g., 10 for every 10 seconds/minutes).
        :param timezone: Optional timezone for specific scheduled times.
        """
        self.frequency = frequency
        self.job_time = job_time
        self.interval = interval
        self.timezone = timezone
        self.processor = LogProcessor()  # Instantiate the LogProcessor class
        self.start()

    def start(self):
        """
        Start the log processing scheduler based on the specified conditions.
        """
        # Schedule the job based on the frequency
        self.schedule_job()

        logger.info("Scheduler started. Processing logs based on the specified schedule...")

        # Continuously run pending jobs
        while True:
            schedule.run_pending()
            time.sleep(1)  # Sleep for a second between checks

    def schedule_job(self):
        """
        Schedule the job based on the specified frequency and conditions.
        """
        if self.frequency == 'seconds' and self.interval:
            schedule.every(self.interval).seconds.do(self.log_processor_task)
        elif self.frequency == 'minutes' and self.interval:
            schedule.every(self.interval).minutes.do(self.log_processor_task)
        elif self.frequency == 'hour':
            schedule.every().hour.do(self.log_processor_task)
        elif self.frequency == 'daily' and self.job_time:
            schedule.every().day.at(self.job_time).do(self.log_processor_task)
        elif self.frequency == 'weekly' and self.job_time:
            schedule.every().week.at(self.job_time).do(self.log_processor_task)
        else:
            logger.warning("Invalid scheduling conditions provided.")

    def log_processor_task(self):
        """
        The scheduled task that will run to process logs.
        """
        logger.info("Starting log processing task...")
        self.processor.run()  # Execute the run method
        logger.info("Log processing task completed.")
