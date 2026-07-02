from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import settings
from app.features.auth.models import User, UserOTP
from app.features.auth.schemas import UserRegister

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashes a raw password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Queries user by email address."""
    return db.query(User).filter(User.email == email.strip().lower()).first()

def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
    """Queries user by phone number."""
    return db.query(User).filter(User.phone_number == phone.strip()).first()

def create_user(db: Session, user_data: UserRegister) -> User:
    """Creates a new user account."""
    hashed_pwd = hash_password(user_data.password)
    db_user = User(
        email=user_data.email.strip().lower() if user_data.email else None,
        phone_number=user_data.phone_number.strip() if user_data.phone_number else None,
        hashed_password=hashed_pwd
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def generate_otp_for_phone(db: Session, phone_number: str) -> str:
    """Generates and stores an OTP code (mock 0000 code for local dev)."""
    otp_code = "0000"  # Mock OTP
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    otp_entry = UserOTP(
        phone_number=phone_number,
        otp_code=otp_code,
        expires_at=expires_at
    )
    db.add(otp_entry)
    db.commit()
    return otp_code

def verify_otp_code(db: Session, phone_number: str, otp_code: str) -> bool:
    """Verifies a phone OTP code."""
    otp_record = db.query(UserOTP).filter(
        UserOTP.phone_number == phone_number,
        UserOTP.otp_code == otp_code,
        UserOTP.is_used == False,
        UserOTP.expires_at > datetime.utcnow()
    ).order_by(UserOTP.created_at.desc()).first()

    if otp_record:
        otp_record.is_used = True
        db.commit()
        return True
    return False


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Verifies access token and returns the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
