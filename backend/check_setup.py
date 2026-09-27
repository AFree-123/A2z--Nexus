r"""Quick local setup diagnostic for A2Z Nexus.

Run from backend:
    .\.venv\Scripts\python.exe check_setup.py

No credential values are printed.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.settings import settings  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
print("A2Z Nexus backend setup check")
print("-" * 36)
print(f"Project root : {ROOT}")
print(f"Provider     : {settings.AI_PROVIDER}")
print(f"Gemini key   : {'OK' if settings.GEMINI_API_KEY.strip() else 'MISSING'}")
print(f"Gemini model : {settings.GEMINI_MODEL}")
print(f"GitHub token : {'OK' if settings.GITHUB_TOKEN.strip() else 'optional/missing'}")
print(f"Google OAuth : {'OK' if settings.GOOGLE_CLIENT_ID.strip() and settings.GOOGLE_CLIENT_SECRET.strip() else 'optional/missing'}")
print(f"Microsoft    : {'OK' if settings.MICROSOFT_CLIENT_ID.strip() and settings.MICROSOFT_CLIENT_SECRET.strip() else 'optional/missing'}")
print(f"Database     : {settings.DATABASE_URL}")
print(f"Frontend     : {settings.FRONTEND_URL}")
print(f"Port         : {settings.BACKEND_PORT}")
print()
if settings.AI_PROVIDER.lower().strip() == "gemini" and not settings.GEMINI_API_KEY.strip():
    print("ACTION: Put your Gemini API key in the project-root .env and restart the backend.")
else:
    print("Configuration looks ready for startup.")
