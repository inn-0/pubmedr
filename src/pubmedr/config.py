import json
import logging
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s",
)
def custom_logger(name):
    return logging.getLogger(name)

def read_api_keys():
    env_path = Path(__file__).parent.parent.parent.joinpath(".env")
    with env_path.open("r") as file:
        env = json.load(file)
    return env


api_keys = read_api_keys()
os.environ["NCBI_API_KEY"] = api_keys["API_KEY_NCBI"]  # needs to be set globally like this
os.environ["LOGFIRE_TOKEN"] = api_keys["API_KEY_LOGFIRE"]

API_KEY_OPENAI = api_keys["API_KEY_OPENAI"]
GOOGLE_CLOUD_CREDENTIALS = api_keys["GOOGLE_CLOUD_CREDENTIALS"]


logger = custom_logger(__name__)
logger.debug("Config initialized with API keys")
