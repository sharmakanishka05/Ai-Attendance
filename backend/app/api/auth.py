from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import User
from app.schemas import Token, LoginRequest, UserResponse
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Development fallback only
        if settings.APP_ENV != "production" and plain_password == hashed_password:
            return True
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_token_from_request(request: Request, bearer_token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Retrieves token from Authorization Bearer header OR HTTP-only cookie"""
    if bearer_token:
        return bearer_token
    cookie_token = request.cookies.get("auth_token")
    if cookie_token:
        return cookie_token
    return None

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Strict user authentication.
    Does NOT assume or default to admin in any production path.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
        
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user

def require_authenticated_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """Enforces authentication; raises 401 if missing or invalid"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

def require_role(allowed_roles: List[str]):
    """Enforces strict role-based access control; raises 403 if unauthorized"""
    def role_checker(user: User = Depends(require_authenticated_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. This action requires one of the following roles: {', '.join(allowed_roles)}.",
            )
        return user
    return role_checker

require_admin = require_role(["admin"])
require_teacher_or_admin = require_role(["admin", "teacher"])

@router.post("/login", response_model=Token)
def login(login_req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_req.email).first()
    if not user or not verify_password(login_req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact your administrator.",
        )

    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role}
    )

    # Set secure HTTP-only cookie for browser sessions
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite=settings.cookie_samesite_policy,
        secure=settings.cookie_secure_policy,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="auth_token",
        httponly=True,
        samesite=settings.cookie_samesite_policy,
        secure=settings.cookie_secure_policy,
    )
    return {"success": True, "message": "Logged out successfully."}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: User = Depends(require_authenticated_user)):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active
    }
