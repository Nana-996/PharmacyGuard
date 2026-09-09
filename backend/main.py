import os
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.agent.pharmacy_agent import run_pharmacy_agent
from backend.tools.prescription_tool import get_prescription
from backend.api.auth import router as auth_router
from backend.api.prescriptions import router as prescriptions_router
from backend.api.reviews import router as reviews_router
from backend.api.inventory import router as inventory_router
from backend.api.analytics import router as analytics_router
from backend.api.student import router as student_router
from backend.auth.dependencies import require_roles

app = FastAPI(
    title="PharmacyGuard API",
    description="Backend API and Strands Agent service for PharmacyGuard operations and human pharmacist review workflows.",
    version="0.3.0"
)

# Configurable CORS origins with secure local defaults
cors_env = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

from fastapi.responses import JSONResponse
from backend.security.demo_guard import (
    demo_rate_limiter,
    demo_quota_tracker,
    get_client_identifier,
    DEMO_RATE_LIMIT_ENABLED,
)

# Demo Protection: Sliding-Window IP Rate Limiter
@app.middleware("http")
async def demo_rate_limit_middleware(request: Request, call_next):
    # Allow preflights, docs, and health check without rate limiting
    if request.method == "OPTIONS" or request.url.path in ("/health", "/docs", "/openapi.json"):
        return await call_next(request)

    client_id = get_client_identifier(request)
    allowed, used, remaining = demo_rate_limiter.check_rate_limit(client_id)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded. Please wait 60 seconds before making additional requests in this competition demo.",
                "retry_after": 60,
                "client_id": client_id
            },
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(demo_rate_limiter.max_requests),
                "X-RateLimit-Remaining": "0"
            }
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(demo_rate_limiter.max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response

# Register API routers
app.include_router(auth_router)
app.include_router(prescriptions_router)
app.include_router(reviews_router)
app.include_router(inventory_router)
app.include_router(analytics_router)
app.include_router(student_router)


def get_environment_mode() -> str:
    """Returns deployment environment mode (e.g. competition_demo, production, staging, local_development)."""
    return os.getenv(
        "ENVIRONMENT",
        os.getenv(
            "APP_ENV",
            os.getenv("PHARMACYGUARD_ENV", "competition_demo" if DEMO_RATE_LIMIT_ENABLED else "local_development")
        )
    ).strip().lower()


@app.get("/api/demo/quota")
def get_demo_quota_endpoint(request: Request):
    """Returns the current IP/session remaining AI agent verification quota for the public competition demo."""
    client_id = get_client_identifier(request)
    quota = demo_quota_tracker.get_quota(client_id)
    return {
        "status": "success",
        "demo_mode": DEMO_RATE_LIMIT_ENABLED,
        "environment": get_environment_mode(),
        "client_id": client_id,
        "quota": quota,
        "disclaimer": "Competition Demonstration Sandbox: All clinical compendia and EHR data are synthetic. Zero AWS credentials exposed to browser."
    }


PHARMACIST_ROLES = ["STAFF_PHARMACIST", "CHIEF_PHARMACIST"]


class AgentTestRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message prompt to send to the PharmacyGuard agent")


class AgentTestResponse(BaseModel):
    response: str
    status: str = "success"


@app.get("/health")
def health_check():
    """Health check endpoint to verify backend service status (Public)."""
    return {
        "status": "healthy",
        "service": "PharmacyGuard Backend",
        "version": "0.3.0",
        "mode": get_environment_mode()
    }


@app.post("/api/agent/test", response_model=AgentTestResponse)

def test_agent_endpoint(
    request: AgentTestRequest,
    current_user: Dict[str, Any] = Depends(require_roles(PHARMACIST_ROLES))
):
    """
    Test endpoint to invoke the Strands PharmacyGuard operations agent backed by Amazon Bedrock.
    """
    try:
        agent_output = run_pharmacy_agent(request.message)
        return AgentTestResponse(response=agent_output, status="success")
    except Exception as e:
        error_msg = str(e)
        if "Credentials" in error_msg or "NoCredentialsError" in error_msg or "UnrecognizedClientException" in error_msg or "AccessDenied" in error_msg:
            raise HTTPException(
                status_code=500,
                detail=f"AWS Bedrock authentication error: {error_msg}. Please ensure AWS_BEARER_TOKEN_BEDROCK is configured in your .env file."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error invoking PharmacyGuard agent: {error_msg}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
