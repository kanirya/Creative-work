"""
Start the LMS scraper service on port 8002.
Run: python start_lms_scraper.py
"""
import sys
import os
from pathlib import Path

# Add services/lms-scraper to path
sys.path.insert(0, "services/lms-scraper")

# Set required env vars
os.environ.setdefault("MS_EMAIL", "muhammad.141510.isb@iqra.edu.pk")
os.environ.setdefault("MS_PASSWORD", "Bree@4u4u")
os.environ.setdefault("LMS_BASE_URL", "https://lms.iqra.edu.pk")
os.environ.setdefault("SESSION_STORAGE_PATH", str(Path("lms_session_test.json").absolute()))
os.environ.setdefault("API_GATEWAY_URL", "http://localhost:5000")
os.environ.setdefault("DATABASE_URL", "postgresql://edupilot:password@localhost:5432/edupilot")
os.environ.setdefault("OPENAI_API_KEY", "sk-placeholder")
os.environ.setdefault("EMBEDDING_MODEL", "text-embedding-3-small")

import uvicorn
uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=False)
