"""
SIH 2026 — PS26103 | Authentication Router
==========================================
Handles user login, JWT issuance, and profile retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.models.project import User
from backend.app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from backend.app.core.security import verify_password, create_access_token
from backend.app.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email and password to receive a JWT access token.
    Default credentials:
      - Admin: admin@mospi.gov.in / Admin@123
      - Analyst: analyst@mospi.gov.in / Analyst@123
    """
    stmt = select(User).where(User.email == request.email.lower().strip())
    user = db.execute(stmt).scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email, "role": user.role})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get profile details of the authenticated user.
    """
    return current_user

