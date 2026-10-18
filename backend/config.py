import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if present
load_dotenv(BASE_DIR / ".env")

class Settings:
    APP_NAME: str = "MediProcure AI API"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    API_KEY: str = os.getenv("MEDIPROCURE_API_KEY", "mediprocure-local-dev-key")
    SEED_DEMO_DATA: bool = os.getenv(
        "SEED_DEMO_DATA", "true" if APP_ENV == "development" else "false"
    ).lower() in {"1", "true", "yes", "on"}
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'mediprocure.db'}")
    
    # Gmail / Agent mode: "SIMULATED" or "LIVE"
    GMAIL_MODE: str = os.getenv("GMAIL_MODE", "SIMULATED").upper()
    
    # CORS Origins (supporting standard React Vite dev origins 5173 and 3000)
    _raw_cors = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )
    CORS_ORIGINS: list[str] = [origin.strip() for origin in _raw_cors.split(",") if origin.strip()]

settings = Settings()
