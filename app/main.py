from typing import Optional
from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session
from app.database import engine,get_db,Base
from app import models

#Base.metadata.create_all(bind=engine)
app = FastAPI()

@app.get("/")
def index():
  return "HEllo"

@app.post("/items/")
def create_item(name:str,description: Optional[str] = None, db:Session = Depends(get_db)):
  item = models.Item(name=name,description=description)
  db.add(item)
  db.commit()
  db.refresh(item)
  return item

@app.get("/items/")
def list_items(db: Session = Depends(get_db)):
  return db.query(models.Item).all()