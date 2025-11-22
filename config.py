# config.py
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env in project root

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "hospital_db"),
    "raise_on_warnings": True
}

FLASK_SECRET = os.getenv("FLASK_SECRET", "dev-secret-change-me")
