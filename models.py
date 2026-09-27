from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    bookings = relationship("Booking", back_populates="user")

class DiagnosticCentre(Base):
    __tablename__ = "diagnostic_centres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    tests = relationship("DiagnosticTest", back_populates="centre")
    bookings = relationship("Booking", back_populates="centre")

class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    centre_id = Column(
    	Integer,
    	ForeignKey("diagnostic_centres.id"),
    	nullable=False
    )
    centre = relationship("DiagnosticCentre", back_populates="tests")
    bookings = relationship("Booking", back_populates="test")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    test_id = Column(
        Integer,
        ForeignKey("diagnostic_tests.id"),
        nullable=False
    )

    centre_id = Column(
        Integer,
        ForeignKey("diagnostic_centres.id"),
        nullable=False
    )

    appointment_datetime = Column(
        DateTime,
        nullable=False
    )

    amount = Column(
        Integer,
        nullable=False
    )

    status = Column(
        String,
        nullable=False,
        default="PENDING"
    )
    user = relationship("User", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False)
    test = relationship("DiagnosticTest", back_populates="bookings")
    centre = relationship("DiagnosticCentre", back_populates="bookings")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)

    amount = Column(Integer, nullable=False)

    status = Column(
        String,
        nullable=False
    )

    event_id = Column(
        String,
        unique=True,
        nullable=False
    )
    booking = relationship("Booking", back_populates="payment")