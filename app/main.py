from typing import Optional
from fastapi import FastAPI,Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import engine,get_db,Base
from app import models
from pathlib import Path
from fastapi.responses import HTMLResponse

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

@app.get("/links/")
def list_links(db: Session = Depends(get_db)):
  return db.query(models.NetworkLink).order_by(models.NetworkLink.last_seen.desc()).all()


@app.get("/containers/")
def list_containers(db: Session = Depends(get_db)):
  return db.query(models.Container).order_by(models.Container.name).all()


@app.get("/topology/")
def get_topology(db: Session = Depends(get_db)):
  hosts = db.query(models.DiscoveredHost).all()
  links = db.query(models.NetworkLink).all()

  nodes = [
    {
      "id": h.ip,
      "label": h.hostname or h.ip,
      "title": f"{h.ip}\n{h.vendor or 'Unknown vendor'}\n{h.os_guess or 'OS unknown'}",
      "status": h.status,
    }
    for h in hosts
  ]
  edges = [{"from": l.source_ip, "to": l.target_ip, "type": l.link_type} for l in links]

  return {"nodes": nodes, "edges": edges}


@app.get("/topology/view", response_class=HTMLResponse)
def topology_view():
  return (Path(__file__).parent / "topology.html").read_text(encoding="utf-8")