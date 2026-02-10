import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("AGENT_PORT", 5005))
HOST = "127.0.0.1"
ROOT_DIR = os.getenv("ROOT_DIR", "")
TOKEN_SECRET = os.getenv("AGENT_TOKEN", "dev-token-change-in-production")
DEBUG = os.getenv("AGENT_DEBUG", "false").lower() == "true"
