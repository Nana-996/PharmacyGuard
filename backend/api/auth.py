"""
FastAPI router for PharmacyGuard Authentication & Session Management.
Provides endpoints for login, logout, session verification, and user profile inspection.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field

from backend.data.database import (
    get_user_by_email,
    update_user_last_login,
    insert_audit_event
)
from backend.auth.security import verify_password, create_access_token
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, description="User email address")
    password: str = Field(..., min_length=1, description="User plaintext password")



class UserResponse(BaseModel):
    user_id: str
    full_name: str
    email: str
    role: str
    active: int
    created_at: str
    last_login_at: Optional[str] = None


class LoginResponse(BaseModel):
    status: str
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/login", response_model=LoginResponse)
def login_endpoint(payload: LoginRequest) -> Dict[str, Any]:
    """
    Authenticates a user via email and password, generates a signed JWT token,
    updates last login timestamp, and records audit event.
    """
    clean_email = payload.email.strip().lower()
    user = get_user_by_email(clean_email)

    if not user or not verify_password(payload.password, user["password_hash"]):
        # Log failed authentication attempt in immutable audit trail
        ts = datetime.now(timezone.utc).isoformat()
        insert_audit_event(
            event_type="LOGIN_FAILURE",
            actor_type="USER",
            actor_id=user["user_id"] if user else "UNKNOWN",
            prescription_id="N/A",
            event_data=json.dumps({"email": clean_email, "reason": "Invalid credentials"}),
            timestamp=ts
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deactivated. Contact the system administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login time
    update_user_last_login(user["user_id"])

    # Create session JWT token
    token_payload = {
        "sub": user["user_id"],
        "email": user["email"],
        "role": user["role"],
        "full_name": user["full_name"],
    }
    access_token = create_access_token(token_payload)

    # Log successful login in immutable audit trail
    ts = datetime.now(timezone.utc).isoformat()
    insert_audit_event(
        event_type="LOGIN_SUCCESS",
        actor_type="USER",
        actor_id=user["user_id"],
        prescription_id="N/A",
        event_data=json.dumps({
            "email": user["email"],
            "role": user["role"],
            "full_name": user["full_name"]
        }),
        timestamp=ts
    )

    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "active": user["active"],
            "created_at": user["created_at"],
            "last_login_at": ts
        }
    }


@router.post("/logout")
def logout_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Logs out the authenticated user and records an audit event.
    """
    ts = datetime.now(timezone.utc).isoformat()
    insert_audit_event(
        event_type="LOGOUT",
        actor_type="USER",
        actor_id=current_user["user_id"],
        prescription_id="N/A",
        event_data=json.dumps({
            "email": current_user["email"],
            "role": current_user["role"]
        }),
        timestamp=ts
    )
    return {
        "status": "success",
        "message": "User session closed successfully."
    }


@router.get("/me", response_model=Dict[str, Any])
def get_me_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Returns the authenticated user's profile and assigned role.
    """
    return {
        "status": "success",
        "data": {
            "user_id": current_user["user_id"],
            "full_name": current_user["full_name"],
            "email": current_user["email"],
            "role": current_user["role"],
            "active": current_user["active"],
            "created_at": current_user["created_at"],
            "last_login_at": current_user.get("last_login_at")
        }
    }
