import os
import logging
import django
from django.conf import settings
from django.contrib.auth.models import User  # Import User model to handle user lookups
from common_django.logging_app.models import RequestLog  # Adjust according to your project structure
import ast
import re
from django.utils.functional import SimpleLazyObject
# from django.db import IntegrityError
import hashlib
from django.utils import timezone
from datetime import datetime
import pytz

# # Setup Django if not already done
# def setup_django():
#     if not settings.configured:
#         os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lcim.settings')
#         django.setup()

# Logger for this module
logger = logging.getLogger('log_processor')

# Path to the log file you wish to read
LOG_FILE_PATH = settings.BASE_DIR / 'logs/request_logs.log'

print('Log file path:', LOG_FILE_PATH)


class LogProcessor:
    def __init__(self, log_file_path=LOG_FILE_PATH):
        self.log_file_path = log_file_path
        # setup_django()  # Ensure Django is set up before processing logs

    def process_logs(self):
        """
        Reads and processes logs from the log file and saves entries to the database.
        """
        if not os.path.exists(self.log_file_path):
            logger.warning(f"Log file does not exist at {self.log_file_path}.")
            return

        try:
            with open(self.log_file_path, 'r') as log_file:
                log_lines = log_file.readlines()

            if not log_lines:
                logger.info("No new logs to process.")
                return

            # Process each log entry
            for log_line in log_lines:
                log_data = self.parse_log(log_line)
                if log_data:
                    # Save the log entry to the database
                    self.save_log_to_db(log_data)
        except IOError as e:
            logger.error(f"Error reading log file {self.log_file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while processing logs: {e}")

    def parse_log(self, log_line):
        """
        Parse the log line and extract relevant details.
        """
        try:
            # Extract the part after "Request:" or "Response:" and ensure it's properly formatted
            log_start_idx = log_line.find("{")
            if log_start_idx == -1:
                logger.error(f"Invalid log line format: No log data found in line: {log_line.strip()}")
                return None

            log_data_str = log_line[log_start_idx:]  # Extract the string containing the dictionary

            # Handle potential issues with quotes and Django-specific objects
            log_data_str = self.preprocess_log_data(log_data_str)

            # Use ast.literal_eval to safely parse the dictionary string into a Python dictionary
            log_data = ast.literal_eval(log_data_str)

            # Handle Django-specific objects, like SimpleLazyObject
            log_data = self.clean_log_data(log_data)

            # Check that the log data has the required fields
            required_fields = ['timestamp', 'url', 'method', 'user', 'remote_ip', 'app_name', 'view', 'class_name', 'function_name', 'line_number']
            if not all(key in log_data for key in required_fields):
                logger.error(f"Missing required fields in log data: {log_data}")
                return None

            return log_data

        except (ValueError, SyntaxError) as e:
            logger.error(f"Error parsing log line: {e} (Line: {log_line.strip()})")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while parsing log line: {e} (Line: {log_line.strip()})")
            return None

    def preprocess_log_data(self, log_data_str):
        """
        Preprocess the log data string to make it JSON-like and easier to parse:
        - Replace single quotes with double quotes
        - Replace Django's SimpleLazyObject and User representations
        """
        # Replace single quotes with double quotes
        log_data_str = log_data_str.replace("'", "\"")

        # Handle SimpleLazyObject
        log_data_str = re.sub(r'<SimpleLazyObject: <User: (.*?)>>', r'"\1"', log_data_str)

        # Handle Django User objects (replace <User: ...> with the email or username inside it)
        log_data_str = re.sub(r'<User: (.*?)>', r'"\1"', log_data_str)

        # Handle other non-JSON compliant structures (if any)
        # Add more replacements if needed for other Django-specific log entries

        return log_data_str

    def clean_log_data(self, log_data):
        """
        Unwraps and cleans up the log data before saving it to the database.
        - Specifically handles `SimpleLazyObject` for the `user` field.
        """
        # Unwrap SimpleLazyObject for the `user` field if it's present
        if isinstance(log_data.get('user'), SimpleLazyObject):
            log_data['user'] = str(log_data['user'].get_user())  # Unwrap the SimpleLazyObject and access the user

        # If the 'user' field is not available, check if it's a string (e.g. Anonymous user)
        elif isinstance(log_data.get('user'), str) and log_data['user'].startswith('<SimpleLazyObject:'):
            log_data['user'] = str(log_data['user']).split('>')[1].strip()

        # Handle missing user field gracefully
        if log_data.get('user') == 'Anonymous':
            log_data['user'] = None

        # Return the cleaned log data
        return log_data

    def save_log_to_db(self, log_data):
        """
        Save the log data to the RequestLog model in the database.
        """
        try:
            # Ensure the 'user' field is a valid User instance or None
            user = log_data.get('user')
            if user:
                user_instance = User.objects.filter(email=user).first()
            else:
                user_instance = None

            # Parse the timestamp correctly
            timestamp_str = log_data.get('timestamp', '')
            try:
                # Remove the 'UTC' and convert the string to a valid datetime object
                if 'UTC' in timestamp_str:
                    timestamp_str = timestamp_str.replace(' UTC', '')
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                # Assign the timestamp to the UTC timezone
                timestamp = timezone.make_aware(timestamp, pytz.UTC)
            except ValueError as e:
                logger.error(f"Invalid timestamp format: {timestamp_str}. Error: {e}")
                return  # Skip saving this entry

            # Save log data to the database
            log_data_to_save = {
                'timestamp': timestamp,
                'method': log_data.get('method'),
                'url': log_data.get('url'),
                'remote_ip': log_data.get('remote_ip'),
                'request_params': log_data.get('request_params'),
                'app_name': log_data.get('app_name', 'Unknown'),
                'view': log_data.get('view', 'Unknown'),
                'class_name': log_data.get('class_name', 'Unknown'),
                'function_name': log_data.get('function_name', 'Unknown'),
                'line_number': log_data.get('line_number', 'Unknown'),
                'user': user_instance,  # Use the actual User instance if found
            }

            # Generate a hash for the log entry to prevent duplicates
            log_hash = hashlib.sha256(str(log_data_to_save).encode('utf-8')).hexdigest()

            # Check for duplicate entry before saving
            if not RequestLog.objects.filter(log_hash=log_hash).exists():
                # Create a new log entry in the database
                RequestLog.objects.create(**log_data_to_save, log_hash=log_hash)
                logger.info(f"Processed log entry: {log_data_to_save['timestamp']}")
            else:
                logger.info(f"Duplicate log entry found for {log_data_to_save['timestamp']}")

        except Exception as e:
            logger.error(f"Error saving log entry to database: {e} (Log Data: {log_data})")

    def run(self):
        """
        The method to start the log processing task.
        """
        logger.info("Starting log processing task...")
        self.process_logs()
        logger.info("Log processing task completed.")
