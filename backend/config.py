import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'cvmanager.db'}")

SECRET_KEY = os.getenv("SECRET_KEY", "cv-manager-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BACKEND_DIR / "uploads")))
RESUME_UPLOAD_DIR = Path(os.getenv("RESUME_UPLOAD_DIR", str(UPLOAD_DIR / "resumes")))
ATTACHMENT_UPLOAD_DIR = Path(os.getenv("ATTACHMENT_UPLOAD_DIR", str(UPLOAD_DIR / "attachments")))

RESUME_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ATTACHMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

CONFIDENCE_THRESHOLD = 0.8
