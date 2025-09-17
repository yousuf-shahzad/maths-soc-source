# app/safety.py
import os
def assert_not_production(context: str):
    indicators = {
        os.getenv("APP_ENVIRONMENT", "").lower(),
        os.getenv("FLASK_ENV", "").lower(),
        os.getenv("ENV", "").lower(),
    }
    if any(v in ("prod", "production") for v in indicators):
        raise RuntimeError(f"Refusing '{context}' in production environment.")