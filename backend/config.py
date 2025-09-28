import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/data_agent")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-3.5-turbo-16k")

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"xlsx", "xls"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Visualization settings
MAX_ROWS_FOR_VISUALIZATION = 10000
DEFAULT_CHART_HEIGHT = 400
DEFAULT_CHART_WIDTH = 800