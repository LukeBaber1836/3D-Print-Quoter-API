from pathlib import Path
import os
from pydantic_settings import BaseSettings

# Constants for file paths and bucket names
LOCAL_DIR = Path("./app/db/temp")

# Bucket names
BUCKET_STL_FILES = "stl-files"
BUCKET_GCODE_FILES = "gcode-files"

class Settings(BaseSettings):
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Supabase Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

settings = Settings()