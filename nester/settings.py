from dotenv import load_dotenv
import os

# Load project-root .env if present
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN", "CHANGE_ME")  # replace in production
SQL_CONN = os.getenv("SQL_CONN")  # optional, only if persistence is enabled
LOG_DIR = os.getenv("LOG_DIR", "logs")
