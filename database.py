from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# ----------------------------------
# FORCE ABSOLUTE PATH (CRITICAL FIX)
# ----------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{BASE_DIR}/cyberclinic.db"

# ----------------------------------
# ENGINE
# ----------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)

# ----------------------------------
# SESSION
# ----------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ----------------------------------
# BASE MODEL
# ----------------------------------
Base = declarative_base()

# ----------------------------------
# DB DEPENDENCY (FASTAPI)
# ----------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()