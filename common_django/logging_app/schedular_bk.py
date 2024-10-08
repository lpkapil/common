import os
import django
import sys
from django.conf import settings

# # Set the DJANGO_SETTINGS_MODULE environment variable to your project settings
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lcim.settings')

# sys.path.append("../../../../../") #here store is root folder(means parent).
# django.setup()

import schedule
import time
import logging
from common_django.logging_app.log_processor import LogProcessor  # Import your class-based log processor

# Set up logger
logger = logging.getLogger('log_scheduler')


def start_scheduler():
    """
    Schedules the log processor task to run every minute.
    """
    # Schedule the task every minute
    schedule.every(1).minute.do(log_processor_task)
    
    logger.info("Scheduler started. Processing logs every minute...")

    # Continuously run pending jobs
    while True:
        schedule.run_pending()
        time.sleep(1)  # Sleep for a second between checks


def log_processor_task():
    """
    The scheduled task that will run every minute to process logs.
    """
    logger.info("Starting log processing task...")
    processor = LogProcessor()  # Instantiate the LogProcessor class
    processor.run()  # Execute the run method
    logger.info("Log processing task completed.")


# if __name__ == "__main__":
#     start_scheduler()
