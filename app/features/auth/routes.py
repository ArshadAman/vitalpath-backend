from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.features.auth.schemas import UserRegister, UserLogin, OTPRequest, OTPVerify, Token, UserResponse
from app.features.auth.services import (
    get_user_by_email, get_user_by_phone, create_user, verify_password,
    create_access_token, generate_otp_for_phone, verify_otp_code
)
from app.features.auth.tasks import send_otp_task

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if user_data.email and get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_data.phone_number and get_user_by_phone(db, user_data.phone_number):
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    return create_user(db, user_data)

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = None
    if login_data.email:
        user = get_user_by_email(db, login_data.email)
    elif login_data.phone_number:
        user = get_user_by_phone(db, login_data.phone_number)

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email/phone or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

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
    return {"access_token": access_token, "token_type": "bearer"}
