import logging

# Configure a custom logger
logger = logging.getLogger('common')
logger.setLevel(logging.DEBUG)

# Create file handler and formatter
file_handler = logging.FileHandler('app_logs.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to the logger
logger.addHandler(file_handler)

def log_message(message):
    """
    Log a message to a file using the custom logger.

    Args:
    - message: The message to be logged.
    """
    logger.info(message)
