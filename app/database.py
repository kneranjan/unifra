import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@db:5432/unifra_db")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autoflush=False,autocommit=False,bind=engine)

Base = declarative_base()

#dependancy for FASTAPI routes

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()  