# Diagnostic Booking System

A backend service for diagnostic test bookings and simulated payments, built using FastAPI and PostgreSQL.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- JWT Authentication
- Docker
- Pytest

## Features

- User signup and login
- JWT-based authentication
- Diagnostic centre management
- Diagnostic test management
- Test booking
- Mock payment processing
- Payment webhook handling
- Idempotent payment webhooks
- Input validation
- Unauthorized access protection
- Automated API tests

## Project Structure

```text
diagnostic-booking-system/
|-- alembic/
|   `-- versions/
|-- tests/
|   `-- test_api.py
|-- database.py
|-- main.py
|-- models.py
|-- schemas.py
|-- docker-compose.yml
|-- alembic.ini
|-- requirements.txt
|-- .gitignore
`-- README.md