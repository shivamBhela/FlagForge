from datetime import datetime, timezone
from fastapi import FastAPI
import random

app = FastAPI(title="FlagForge Demo Instrumented App", version="1.0.0")

@app.get("/healthz")
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "flagforge-demo-app",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/checkout")
def checkout(user_id: str = "user-123"):
    # Simulated feature flag telemetry emitting endpoint
    is_canary = random.random() < 0.25
    return {
        "checkout_version": "v2_canary" if is_canary else "v1_legacy",
        "status": "success",
        "feature_flag": "checkout_v2_redesign",
        "user_id": user_id
    }
