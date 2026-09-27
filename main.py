from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
import os

from dotenv import load_dotenv
from uuid import uuid4
from jose import jwt

load_dotenv()

from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import engine, SessionLocal, Base
from models import User, DiagnosticCentre, DiagnosticTest, Booking, Payment
from schemas import (
    UserCreate,
    CentreCreate,
    TestCreate,
    BookingCreate,
    PaymentCreate,
    PaymentWebhook
)

app = FastAPI()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30



# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Database connection for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user



@app.get("/")
def home():
    return {"message": "Diagnostic Booking API is running!"}


@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):

    # Check whether email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = pwd_context.hash(user.password)

    # Create new user
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email
    }

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not pwd_context.verify(
        form_data.password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/centres")
def create_centre(
    centre: CentreCreate,
    db: Session = Depends(get_db)
):
    new_centre = DiagnosticCentre(
        name=centre.name,
        location=centre.location
    )

    db.add(new_centre)
    db.commit()
    db.refresh(new_centre)

    return {
        "message": "Diagnostic centre created successfully",
        "centre_id": new_centre.id,
        "name": new_centre.name,
        "location": new_centre.location
    }

@app.post("/tests")
def create_test(
    test: TestCreate,
    db: Session = Depends(get_db)
):
    # Check if the diagnostic centre exists
    centre = db.query(DiagnosticCentre).filter(
        DiagnosticCentre.id == test.centre_id
    ).first()

    if not centre:
        raise HTTPException(
            status_code=404,
            detail="Diagnostic centre not found"
        )

    new_test = DiagnosticTest(
        name=test.name,
        price=test.price,
        centre_id=test.centre_id
    )

    db.add(new_test)
    db.commit()
    db.refresh(new_test)

    return {
        "message": "Diagnostic test created successfully",
        "test_id": new_test.id,
        "name": new_test.name,
        "price": new_test.price,
        "centre_id": new_test.centre_id
    }

@app.post("/bookings")
def create_booking(
    booking: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the test exists
    test = db.query(DiagnosticTest).filter(
        DiagnosticTest.id == booking.test_id
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Diagnostic test not found"
        )

    # Check if the centre exists
    centre = db.query(DiagnosticCentre).filter(
        DiagnosticCentre.id == booking.centre_id
    ).first()

    if not centre:
        raise HTTPException(
            status_code=404,
            detail="Diagnostic centre not found"
        )

    # Make sure this test belongs to this centre
    if test.centre_id != centre.id:
        raise HTTPException(
            status_code=400,
            detail="Test does not belong to this diagnostic centre"
        )

    # Create booking
    new_booking = Booking(
        user_id=current_user.id,
        test_id=test.id,
        centre_id=centre.id,
        appointment_datetime=booking.appointment_datetime,
        amount=test.price,
        status="PENDING"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return {
        "message": "Booking created successfully",
        "booking_id": new_booking.id,
        "user_id": new_booking.user_id,
        "test_id": new_booking.test_id,
        "centre_id": new_booking.centre_id,
        "appointment_datetime": new_booking.appointment_datetime,
        "amount": new_booking.amount,
        "status": new_booking.status
    }

@app.get("/bookings")
def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id
    ).all()

    return bookings

@app.post("/payments")
def create_payment(
    payment: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find the booking
    booking = db.query(Booking).filter(
        Booking.id == payment.booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    # Make sure the booking belongs to the logged-in user
    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to pay for this booking"
        )

    # Only pending bookings can be paid
    if booking.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Booking is not pending"
        )

    # Validate payment outcome
    outcome = payment.outcome.upper()

    if outcome not in ["SUCCESS", "FAILED"]:
        raise HTTPException(
            status_code=400,
            detail="Outcome must be SUCCESS or FAILED"
        )

    event_id = f"mock_payment_{uuid4().hex}"

    new_payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=outcome,
        event_id=event_id
)

    db.add(new_payment)

    # Update booking status
    if outcome == "SUCCESS":
        booking.status = "CONFIRMED"
    else:
        booking.status = "FAILED"

    db.commit()
    db.refresh(new_payment)

    return {
        "message": "Payment processed successfully",
        "payment_id": new_payment.id,
        "event_id": new_payment.event_id,
        "booking_id": booking.id,
        "amount": new_payment.amount,
        "payment_status": new_payment.status,
        "booking_status": booking.status
    }

@app.post("/payments/webhook/")
def payment_webhook(
    webhook: PaymentWebhook,
    db: Session = Depends(get_db)
):
    # Check whether this event was already processed
    existing_payment = db.query(Payment).filter(
        Payment.event_id == webhook.event_id
    ).first()

    if existing_payment:
        return {
            "message": "Webhook already processed",
            "payment_id": existing_payment.id,
            "booking_id": existing_payment.booking_id,
            "payment_status": existing_payment.status
        }

    # Validate payment outcome
    outcome = webhook.outcome.upper()

    if outcome not in ["SUCCESS", "FAILED"]:
        raise HTTPException(
            status_code=400,
            detail="Outcome must be SUCCESS or FAILED"
        )

    # Find the booking
    booking = db.query(Booking).filter(
        Booking.id == webhook.booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    # Prevent processing a second payment for the same booking
    existing_booking_payment = db.query(Payment).filter(
        Payment.booking_id == booking.id
    ).first()

    if existing_booking_payment:
        raise HTTPException(
            status_code=400,
            detail="Payment already exists for this booking"
        )

    # Create payment record
    new_payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=outcome,
        event_id=webhook.event_id
    )

    db.add(new_payment)

    # Update booking status
    if outcome == "SUCCESS":
        booking.status = "CONFIRMED"
    else:
        booking.status = "FAILED"

    db.commit()
    db.refresh(new_payment)

    return {
        "message": "Webhook processed successfully",
        "payment_id": new_payment.id,
        "booking_id": booking.id,
        "payment_status": new_payment.status,
        "booking_status": booking.status
    }