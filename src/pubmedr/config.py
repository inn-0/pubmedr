import json
import logging
import os
from pathlib import Path

import logfire
from logfire.integrations.logging import LogfireLoggingHandler


def read_api_keys():
    env_path = Path(__file__).parent.parent.parent.joinpath(".env")
    with env_path.open("r") as file:
        env = json.load(file)
    return env


# Read API keys first
api_keys = read_api_keys()
os.environ["NCBI_API_KEY"] = api_keys["API_KEY_NCBI"]  # needs to be set globally like this
os.environ["LOGFIRE_TOKEN"] = api_keys["API_KEY_LOGFIRE"]

API_KEY_OPENAI = api_keys["API_KEY_OPENAI"]
GOOGLE_CLOUD_CREDENTIALS = api_keys["GOOGLE_CLOUD_CREDENTIALS"]
GSHEET_ID = api_keys["GSHEET_ID"]
LOCK_GSHEET = True  # Saving to Google Sheets turns out to be very complicated, so is paused for now

# Configure logfire FIRST, before any logging setup
logfire.configure(
    send_to_logfire="if-token-present",
    service_name="pubmedr",  # Generic service name for all components
)

# Enable Pydantic instrumentation
# logfire.instrument_pydantic()

# Set up logging with logfire handler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s",
    handlers=[LogfireLoggingHandler()],
)


def custom_logger(name: str) -> logging.Logger:
    """Get a logger that's already configured with logfire."""
    return logging.getLogger(name)


# Initialize module logger
logger = custom_logger(__name__)
logger.debug("Config initialized with API keys and logfire logging")
