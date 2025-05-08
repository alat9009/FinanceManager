import logging
import os

# Get the directory where the script is located
app_directory = os.path.dirname(os.path.abspath(__file__))

# Define the log file path in the app directory
log_file_path = os.path.join(app_directory, "app_errors.log")

# Configure logging
logging.basicConfig(
    filename=log_file_path,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
