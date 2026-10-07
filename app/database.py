import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@db:5432/unifra_db")

try:
    if "postgresql" in DATABASE_URL and "db:" in DATABASE_URL:
        # Check if running outside docker container where 'db' hostname doesn't resolve
        import socket
        try:
            socket.gethostbyname("db")
        except socket.gaierror:
            # Fallback to local Postgres exposed on port 5433 when running outside Docker
            DATABASE_URL = DATABASE_URL.replace("db:5432", "127.0.0.1:5433")
            logger.info(f"Using local PostgreSQL fallback: {DATABASE_URL}")

    if "sqlite" in DATABASE_URL:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(DATABASE_URL)

    SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
except Exception as e:
    logger.warning(f"Database connection setup fallback error: {e}")
    # Final fallback to standard localhost port if something goes really wrong
    DATABASE_URL = "postgresql://admin:admin@127.0.0.1:5433/unifra_db"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"DB session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()