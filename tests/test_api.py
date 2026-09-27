import sys
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Diagnostic Booking API is running!"
    }


def test_signup():
    email = f"pytest_{uuid4().hex}@example.com"

    response = client.post(
        "/signup",
        json={
            "name": "Pytest User",
            "email": email,
            "password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "User created successfully"
    assert data["name"] == "Pytest User"
    assert data["email"] == email


def test_duplicate_signup():
    email = f"duplicate_{uuid4().hex}@example.com"

    first_response = client.post(
        "/signup",
        json={
            "name": "Duplicate User",
            "email": email,
            "password": "password123"
        }
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/signup",
        json={
            "name": "Duplicate User",
            "email": email,
            "password": "password123"
        }
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Email already registered"

def test_login():
    email = f"login_{uuid4().hex}@example.com"

    signup_response = client.post(
        "/signup",
        json={
            "name": "Login Test User",
            "email": email,
            "password": "password123"
        }
    )

    assert signup_response.status_code == 200

    response = client.post(
        "/login",
        data={
            "username": email,
            "password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password():
    email = f"wrong_password_{uuid4().hex}@example.com"

    signup_response = client.post(
        "/signup",
        json={
            "name": "Wrong Password User",
            "email": email,
            "password": "password123"
        }
    )

    assert signup_response.status_code == 200

    response = client.post(
        "/login",
        data={
            "username": email,
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_create_booking():
    # Create user
    email = f"booking_{uuid4().hex}@example.com"

    signup_response = client.post(
        "/signup",
        json={
            "name": "Booking Test User",
            "email": email,
            "password": "password123"
        }
    )

    assert signup_response.status_code == 200

    # Login
    login_response = client.post(
        "/login",
        data={
            "username": email,
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create diagnostic centre
    centre_response = client.post(
        "/centres",
        json={
            "name": "Test Diagnostic Centre",
            "location": "Delhi"
        }
    )

    assert centre_response.status_code == 200

    centre_id = centre_response.json()["centre_id"]

    # Create diagnostic test
    test_response = client.post(
        "/tests",
        json={
            "name": "Blood Test",
            "price": 500,
            "centre_id": centre_id
        }
    )

    assert test_response.status_code == 200

    test_id = test_response.json()["test_id"]

    # Create booking
    booking_response = client.post(
        "/bookings",
        headers=headers,
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_datetime": "2026-10-15T10:00:00"
        }
    )

    assert booking_response.status_code == 200

    data = booking_response.json()

    assert data["message"] == "Booking created successfully"
    assert data["test_id"] == test_id
    assert data["centre_id"] == centre_id
    assert data["amount"] == 500
    assert data["status"] == "PENDING"

def test_user_cannot_pay_for_another_users_booking():
    # Create User A
    email_a = f"user_a_{uuid4().hex}@example.com"

    signup_a = client.post(
        "/signup",
        json={
            "name": "User A",
            "email": email_a,
            "password": "password123"
        }
    )

    assert signup_a.status_code == 200

    # Login User A
    login_a = client.post(
        "/login",
        data={
            "username": email_a,
            "password": "password123"
        }
    )

    assert login_a.status_code == 200

    token_a = login_a.json()["access_token"]

    # Create centre
    centre_response = client.post(
        "/centres",
        json={
            "name": "Security Test Centre",
            "location": "Delhi"
        }
    )

    assert centre_response.status_code == 200

    centre_id = centre_response.json()["centre_id"]

    # Create test
    test_response = client.post(
        "/tests",
        json={
            "name": "Security Blood Test",
            "price": 500,
            "centre_id": centre_id
        }
    )

    assert test_response.status_code == 200

    test_id = test_response.json()["test_id"]

    # User A creates booking
    booking_response = client.post(
        "/bookings",
        headers={
            "Authorization": f"Bearer {token_a}"
        },
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_datetime": "2026-10-20T10:00:00"
        }
    )

    assert booking_response.status_code == 200

    booking_id = booking_response.json()["booking_id"]

    # Create User B
    email_b = f"user_b_{uuid4().hex}@example.com"

    signup_b = client.post(
        "/signup",
        json={
            "name": "User B",
            "email": email_b,
            "password": "password123"
        }
    )

    assert signup_b.status_code == 200

    # Login User B
    login_b = client.post(
        "/login",
        data={
            "username": email_b,
            "password": "password123"
        }
    )

    assert login_b.status_code == 200

    token_b = login_b.json()["access_token"]

    # User B tries to pay for User A's booking
    payment_response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {token_b}"
        },
        json={
            "booking_id": booking_id,
            "outcome": "SUCCESS"
        }
    )

    assert payment_response.status_code == 403

    assert payment_response.json()["detail"] == (
        "You are not allowed to pay for this booking"
    )

def test_successful_payment():
    # Create user
    email = f"payment_{uuid4().hex}@example.com"

    signup_response = client.post(
        "/signup",
        json={
            "name": "Payment Test User",
            "email": email,
            "password": "password123"
        }
    )

    assert signup_response.status_code == 200

    # Login
    login_response = client.post(
        "/login",
        data={
            "username": email,
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create diagnostic centre
    centre_response = client.post(
        "/centres",
        json={
            "name": "Payment Test Centre",
            "location": "Delhi"
        }
    )

    assert centre_response.status_code == 200

    centre_id = centre_response.json()["centre_id"]

    # Create diagnostic test
    test_response = client.post(
        "/tests",
        json={
            "name": "Payment Blood Test",
            "price": 500,
            "centre_id": centre_id
        }
    )

    assert test_response.status_code == 200

    test_id = test_response.json()["test_id"]

    # Create booking
    booking_response = client.post(
        "/bookings",
        headers=headers,
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_datetime": "2026-10-25T10:00:00"
        }
    )

    assert booking_response.status_code == 200

    booking_id = booking_response.json()["booking_id"]

    assert booking_response.json()["status"] == "PENDING"

    # Make successful payment
    payment_response = client.post(
        "/payments",
        headers=headers,
        json={
            "booking_id": booking_id,
            "outcome": "SUCCESS"
        }
    )

    assert payment_response.status_code == 200

    data = payment_response.json()

    assert data["booking_id"] == booking_id
    assert data["amount"] == 500
    assert data["payment_status"] == "SUCCESS"
    assert data["booking_status"] == "CONFIRMED"
    assert "payment_id" in data
    assert "event_id" in data

def test_failed_payment():
    # Create user
    email = f"failed_payment_{uuid4().hex}@example.com"

    signup_response = client.post(
        "/signup",
        json={
            "name": "Failed Payment User",
            "email": email,
            "password": "password123"
        }
    )

    assert signup_response.status_code == 200

    # Login
    login_response = client.post(
        "/login",
        data={
            "username": email,
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create diagnostic centre
    centre_response = client.post(
        "/centres",
        json={
            "name": "Failed Payment Centre",
            "location": "Delhi"
        }
    )

    assert centre_response.status_code == 200

    centre_id = centre_response.json()["centre_id"]

    # Create diagnostic test
    test_response = client.post(
        "/tests",
        json={
            "name": "Failed Payment Test",
            "price": 400,
            "centre_id": centre_id
        }
    )

    assert test_response.status_code == 200

    test_id = test_response.json()["test_id"]

    # Create booking
    booking_response = client.post(
        "/bookings",
        headers=headers,
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_datetime": "2026-10-26T10:00:00"
        }
    )

    assert booking_response.status_code == 200

    booking_id = booking_response.json()["booking_id"]

    assert booking_response.json()["status"] == "PENDING"

    # Make failed payment
    payment_response = client.post(
        "/payments",
        headers=headers,
        json={
            "booking_id": booking_id,
            "outcome": "FAILED"
        }
    )

    assert payment_response.status_code == 200

    data = payment_response.json()

    assert data["booking_id"] == booking_id
    assert data["amount"] == 400
    assert data["payment_status"] == "FAILED"
    assert data["booking_status"] == "FAILED"
    assert "payment_id" in data
    assert "event_id" in data


def test_invalid_payment_outcome():
    # Create user
    email = f"invalid_payment_{uuid4().hex}@example.com"

    signup_response = client.post(
        "/signup",
        json={
            "name": "Invalid Payment User",
            "email": email,
            "password": "password123"
        }
    )

    assert signup_response.status_code == 200

    # Login
    login_response = client.post(
        "/login",
        data={
            "username": email,
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create diagnostic centre
    centre_response = client.post(
        "/centres",
        json={
            "name": "Invalid Payment Centre",
            "location": "Delhi"
        }
    )

    assert centre_response.status_code == 200

    centre_id = centre_response.json()["centre_id"]

    # Create diagnostic test
    test_response = client.post(
        "/tests",
        json={
            "name": "Invalid Payment Test",
            "price": 300,
            "centre_id": centre_id
        }
    )

    assert test_response.status_code == 200

    test_id = test_response.json()["test_id"]

    # Create booking
    booking_response = client.post(
        "/bookings",
        headers=headers,
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_datetime": "2026-10-27T10:00:00"
        }
    )

    assert booking_response.status_code == 200

    booking_id = booking_response.json()["booking_id"]

    # Try invalid payment outcome
    payment_response = client.post(
        "/payments",
        headers=headers,
        json={
            "booking_id": booking_id,
            "outcome": "INVALID"
        }
    )

    assert payment_response.status_code == 422

    assert payment_response.json()["detail"][0]["type"] == "literal_error"

def test_invalid_booking_id():
    # Create user
    email = f"invalid_booking_{uuid4().hex}@example.com"

    signup_response = client.post(
        "/signup",
        json={
            "name": "Invalid Booking User",
            "email": email,
            "password": "password123"
        }
    )

    assert signup_response.status_code == 200

    # Login
    login_response = client.post(
        "/login",
        data={
            "username": email,
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Try to pay for a booking that does not exist
    payment_response = client.post(
        "/payments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "booking_id": 999999,
            "outcome": "SUCCESS"
        }
    )

    assert payment_response.status_code == 404
    assert payment_response.json()["detail"] == "Booking not found"

def test_repeated_webhook_is_idempotent():
    # Create user
    email = f"webhook_{uuid4().hex}@example.com"

    signup_response = client.post(
        "/signup",
        json={
            "name": "Webhook Test User",
            "email": email,
            "password": "password123"
        }
    )

    assert signup_response.status_code == 200

    # Login
    login_response = client.post(
        "/login",
        data={
            "username": email,
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create diagnostic centre
    centre_response = client.post(
        "/centres",
        json={
            "name": "Webhook Test Centre",
            "location": "Delhi"
        }
    )

    assert centre_response.status_code == 200

    centre_id = centre_response.json()["centre_id"]

    # Create diagnostic test
    test_response = client.post(
        "/tests",
        json={
            "name": "Webhook Test",
            "price": 600,
            "centre_id": centre_id
        }
    )

    assert test_response.status_code == 200

    test_id = test_response.json()["test_id"]

    # Create booking
    booking_response = client.post(
        "/bookings",
        headers=headers,
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_datetime": "2026-10-28T10:00:00"
        }
    )

    assert booking_response.status_code == 200

    booking_id = booking_response.json()["booking_id"]

    # Send first webhook
    webhook_data = {
        "event_id": f"webhook_event_{uuid4().hex}",
        "booking_id": booking_id,
        "outcome": "SUCCESS"
    }

    first_response = client.post(
        "/payments/webhook/",
        json=webhook_data
    )

    assert first_response.status_code == 200

    first_data = first_response.json()

    assert first_data["message"] == "Webhook processed successfully"
    assert first_data["booking_id"] == booking_id
    assert first_data["payment_status"] == "SUCCESS"
    assert first_data["booking_status"] == "CONFIRMED"

    payment_id = first_data["payment_id"]

    # Send the exact same webhook again
    second_response = client.post(
        "/payments/webhook/",
        json=webhook_data
    )

    assert second_response.status_code == 200

    second_data = second_response.json()

    assert second_data["message"] == "Webhook already processed"
    assert second_data["payment_id"] == payment_id
    assert second_data["booking_id"] == booking_id
    assert second_data["payment_status"] == "SUCCESS"