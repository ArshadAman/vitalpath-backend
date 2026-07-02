from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.core.database import get_db
from app.core.config import settings
from app.features.auth.models import User
from app.features.auth.schemas import (
    UserRegister, UserLogin, OTPRequest, OTPVerify, Token, UserResponse, RefreshTokenRequest, GoogleLoginRequest
)
from app.features.auth.services import (
    get_user_by_email, get_user_by_phone, create_user, verify_password,
    create_access_token, create_refresh_token, generate_otp_for_phone, verify_otp_code
)
from app.features.auth.tasks import send_otp_task

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if user_data.email:
        user_data.email = user_data.email.strip().lower()
        if get_user_by_email(db, user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
    if user_data.phone_number:
        user_data.phone_number = user_data.phone_number.strip()
        if get_user_by_phone(db, user_data.phone_number):
            raise HTTPException(status_code=400, detail="Phone number already registered")
    
    return create_user(db, user_data)

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = None
    if login_data.email:
        login_data.email = login_data.email.strip().lower()
        user = get_user_by_email(db, login_data.email)
    elif login_data.phone_number:
        login_data.phone_number = login_data.phone_number.strip()
        user = get_user_by_phone(db, login_data.phone_number)

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email/phone or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@router.post("/otp/send")
def send_otp(otp_req: OTPRequest, db: Session = Depends(get_db)):
    user = get_user_by_phone(db, otp_req.phone_number)
    if not user:
        raise HTTPException(status_code=400, detail="Phone number not registered. Please sign up first.")
    
    otp_code = generate_otp_for_phone(db, otp_req.phone_number)
    # Trigger asynchronous Celery task to dispatch OTP
    send_otp_task.delay(otp_req.phone_number, otp_code)
    return {"message": "OTP sent successfully"}

@router.post("/otp/verify", response_model=Token)
def verify_otp(verify_data: OTPVerify, db: Session = Depends(get_db)):
    is_valid = verify_otp_code(db, verify_data.phone_number, verify_data.otp_code)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user = get_user_by_phone(db, verify_data.phone_number)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_access_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Validates refresh token and issues a new access token + refresh token pair."""
    try:
        payload = jwt.decode(refresh_data.refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired or invalid refresh token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token, 
        "refresh_token": new_refresh_token, 
        "token_type": "bearer"
    }

@router.post("/google", response_model=Token)
def google_auth(login_data: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Authenticates Google OAuth2 sign-in token payloads."""
    email = login_data.email.strip().lower()
    
    # Query database for user
    user = get_user_by_email(db, email)
    if not user:
        # Register new OAuth user automatically
        user = User(email=email, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Initialize their Health Profile structure
        from app.features.profile.models import HealthProfile
        profile = HealthProfile(user_id=user.id, name=login_data.name)
        db.add(profile)
        db.commit()
    else:
        # Check if they have an active health profile, otherwise create it
        from app.features.profile.models import HealthProfile
        profile = db.query(HealthProfile).filter(HealthProfile.user_id == user.id).first()
        if not profile:
            profile = HealthProfile(user_id=user.id, name=login_data.name)
            db.add(profile)
            db.commit()
        elif login_data.name and not profile.name:
            profile.name = login_data.name
            db.commit()
            
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }
