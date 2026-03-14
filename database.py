import os
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, Float,
                        ForeignKey, Boolean, Text, func)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session

BASE_DIR = os.path.dirname(__file__)
DB_FILENAME = os.path.join(BASE_DIR, "bus_park.db")
DB_URL = f"sqlite:///{DB_FILENAME}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
Base = declarative_base()


class Migration(Base):
    __tablename__ = "migrations"
    id = Column(Integer, primary_key=True)
    version = Column(Integer, nullable=False)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False)
    name = Column(String(128), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Slot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key=True)
    slot_number = Column(Integer, unique=True, nullable=False)
    status = Column(String(32), nullable=False, default="available")
    bus_number = Column(String(64), nullable=True)


class Bus(Base):
    __tablename__ = "buses"
    id = Column(Integer, primary_key=True)
    bus_number = Column(String(64), unique=True, nullable=False)
    bus_type = Column(String(64), nullable=False)
    route = Column(String(128), nullable=True)
    owner = Column(String(128), nullable=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=True)
    entry_time = Column(DateTime, nullable=True)

    slot = relationship("Slot")


class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    role = Column(String(64), nullable=False)
    phone = Column(String(64), nullable=True)
    email = Column(String(128), nullable=True)
    license_number = Column(String(64), nullable=True)
    assigned_bus = Column(String(64), nullable=True)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    bus_number = Column(String(64), nullable=False)
    bus_type = Column(String(64), nullable=False)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    gross_fee = Column(Float, nullable=False)
    discount_pct = Column(Float, nullable=False)
    discount_amt = Column(Float, nullable=False)
    amount_paid = Column(Float, nullable=False)
    pass_used = Column(String(32), nullable=False)
    recorded_by = Column(String(64), nullable=False)
    date = Column(String(32), nullable=False)


def init_db():
    """Create tables, apply migrations, and seed required default data."""
    Base.metadata.create_all(bind=engine)
    _apply_migrations()
    _seed_defaults()


def _apply_migrations():
    session = SessionLocal()
    try:
        migration = session.query(Migration).first()
        current_version = migration.version if migration else 0
        target_version = 1

        if current_version < target_version:
            # Version 1 is initial schema - already created by metadata
            if not migration:
                session.add(Migration(version=target_version))
            else:
                migration.version = target_version
            session.commit()
    finally:
        session.close()


def _seed_defaults():
    session = SessionLocal()
    try:
        # Seed default slots if none exist
        if session.query(Slot).count() == 0:
            for i in range(1, 21):
                session.add(Slot(slot_number=i, status="available", bus_number=None))
            session.commit()

        # Seed default users if none exist
        if session.query(User).count() == 0:
            session.add(User(username="admin", password="admin123", role="Admin", name="Administrator"))
            session.add(User(username="staff", password="staff123", role="Staff", name="Staff Member"))
            session.commit()
    finally:
        session.close()


# Initialize database on import
init_db()
