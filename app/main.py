from typing import Optional
from fastapi import FastAPI,Depends, HTTPException
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

@app.get("/hosts/")
def list_hosts(db: Session = Depends(get_db)):
  return db.query(models.DiscoveredHost).order_by(models.DiscoveredHost.last_seen.desc()).all()


@app.get("/hosts/{ip}")
def get_host(ip: str, db: Session = Depends(get_db)):
  host = db.query(models.DiscoveredHost).filter(models.DiscoveredHost.ip == ip).first()
  if host is None:
    raise HTTPException(status_code=404, detail="Host not found")
  return host