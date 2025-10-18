import logging
import os
from datetime import datetime

# --- Configuration Constants ---
LOG_DIR = "logs"
LOG_FILE_NAME = f"{datetime.now().strftime('%Y-%m-%d')}.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE_NAME)
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(levelname)s | %(asctime)s | %(name)s | %(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str):
    """
    Initializes and configures a logger instance.
    
    The logger outputs messages to both the console (INFO level) 
    and a daily log file (DEBUG level).
    
    Args:
        name: The name of the logger (usually __name__ of the module).
    
    Returns:
        A configured logging.Logger object.
    """
    # 1. Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    # 2. Create the logger
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False  # Prevents messages from going to the root logger twice

    # Check if handlers already exist to prevent duplicate logging
    if not logger.handlers:
        # 3. Define the formatter
        formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

        # 4. Console Handler (for real-time feedback)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO) # Only INFO and higher on console
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 5. File Handler (for persistent storage)
        file_handler = logging.FileHandler(LOG_PATH, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG) # All messages (DEBUG and higher) to file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Example usage (can be removed, but helpful for testing)
if __name__ == "__main__":
    test_logger = setup_logger("test_module")
    test_logger.debug("This is a debug message - only in file.")
    test_logger.info("This is an info message - in console and file.")
    test_logger.warning("A warning occurred.")
    test_logger.error("An error happened!")