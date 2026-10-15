from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import engine, get_db, Base, SessionLocal
from app import models
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.discovery_agent.classify import guess_device_type
from dotenv import load_dotenv
import os
import logging
import threading

logger = logging.getLogger(__name__)

load_dotenv()
GATEWAY_IP = os.getenv("GATEWAY_IP", "")

# Create tables if using SQLite / Postgres
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"Could not create tables automatically: {e}")

app = FastAPI(title="Unifra Hybrid Infrastructure Observability")


class DiscoveryToggle(BaseModel):
    enabled: bool


class HostRename(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class TopologyReset(BaseModel):
    start_scan: bool = True


class DiscoveryScheduler:
    """Runs one discovery pass at a time while the UI scan toggle is enabled."""

    interval_seconds = 30

    def __init__(self):
        self.enabled = False
        self.resetting = False
        self._lock = threading.Lock()
        self._scan_lock = threading.Lock()
        self._wake = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._reset_thread: Optional[threading.Thread] = None
        self._generation = 0

    def set_enabled(self, enabled: bool) -> bool:
        with self._lock:
            if not enabled and self.enabled:
                self._generation += 1
            self.enabled = enabled
            if enabled and (self._thread is None or not self._thread.is_alive()):
                self._wake.clear()
                self._thread = threading.Thread(target=self._run, daemon=True, name="unifra-discovery")
                self._thread.start()
            elif not enabled:
                self._wake.set()
        return self.enabled

    def _run(self):
        from app.discovery_agent.storage import run_scan

        while True:
            with self._lock:
                if not self.enabled:
                    return
                generation = self._generation
                self._wake.clear()
            try:
                # A reset waits for an in-progress scan rather than allowing
                # scan results to be written back after the map is cleared.
                with self._scan_lock:
                    with self._lock:
                        if not self.enabled or generation != self._generation:
                            return
                    run_scan()
            except Exception:
                logger.exception("Discovery scan failed")
            self._wake.wait(self.interval_seconds)

    def request_reset(self, start_scan: bool) -> bool:
        """Queue a reset without blocking the HTTP request on an Nmap scan."""
        with self._lock:
            if self.resetting:
                return False
            self.enabled = False
            self.resetting = True
            self._generation += 1
            self._wake.set()
            self._reset_thread = threading.Thread(
                target=self._reset_worker,
                args=(start_scan,),
                daemon=True,
                name="unifra-topology-reset",
            )
            self._reset_thread.start()
        return True

    def _reset_worker(self, start_scan: bool):
        # Wait for a current scan to finish before deleting its results.
        with self._scan_lock:
            db = SessionLocal()
            try:
                db.query(models.NetworkLink).delete(synchronize_session=False)
                db.query(models.Container).delete(synchronize_session=False)
                db.query(models.DiscoveredHost).delete(synchronize_session=False)
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Topology reset failed")
            finally:
                db.close()
                with self._lock:
                    self.resetting = False
        if start_scan:
            self.set_enabled(True)


discovery_scheduler = DiscoveryScheduler()

# Mount Static Files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    templates_dir = Path(__file__).parent / "templates"
    return (templates_dir / "index.html").read_text(encoding="utf-8")

@app.post("/items/")
def create_item(name: str, description: Optional[str] = None, db: Session = Depends(get_db)):
    item = models.Item(name=name, description=description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/items/")
def list_items(db: Session = Depends(get_db)):
    try:
        return db.query(models.Item).all()
    except Exception as e:
        logger.error(f"Error querying items: {e}")
        return []

@app.get("/hosts/")
def list_hosts(db: Session = Depends(get_db)):
    try:
        return db.query(models.DiscoveredHost).order_by(models.DiscoveredHost.last_seen.desc()).all()
    except Exception as e:
        logger.error(f"Error querying hosts: {e}")
        return []

@app.get("/hosts/{ip}")
def get_host(ip: str, db: Session = Depends(get_db)):
    try:
        host = db.query(models.DiscoveredHost).filter(models.DiscoveredHost.ip == ip).first()
        if host is None:
            raise HTTPException(status_code=404, detail="Host not found")
        return host
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting host {ip}: {e}")
        raise HTTPException(status_code=404, detail="Host not found")


@app.patch("/hosts/{ip}/name")
def rename_host(ip: str, payload: HostRename, db: Session = Depends(get_db)):
    host = db.query(models.DiscoveredHost).filter(models.DiscoveredHost.ip == ip).first()
    if host is None:
        raise HTTPException(status_code=404, detail="Host not found")
    host.hostname = payload.name.strip()
    db.commit()
    db.refresh(host)
    return host


@app.get("/discovery/status")
def discovery_status():
    return {
        "enabled": discovery_scheduler.enabled,
        "resetting": discovery_scheduler.resetting,
        "interval_seconds": discovery_scheduler.interval_seconds,
    }


@app.post("/discovery/toggle")
def toggle_discovery(payload: DiscoveryToggle):
    enabled = discovery_scheduler.set_enabled(payload.enabled)
    return {"enabled": enabled, "interval_seconds": discovery_scheduler.interval_seconds}


@app.post("/discovery/reset", status_code=202)
def reset_topology(payload: TopologyReset):
    """Queue a topology reset; an active scan is allowed to finish safely."""
    queued = discovery_scheduler.request_reset(payload.start_scan)
    return {
        "queued": queued,
        "resetting": discovery_scheduler.resetting,
        "scan_enabled": discovery_scheduler.enabled,
        "interval_seconds": discovery_scheduler.interval_seconds,
    }

@app.get("/links/")
def list_links(db: Session = Depends(get_db)):
    try:
        return db.query(models.NetworkLink).order_by(models.NetworkLink.last_seen.desc()).all()
    except Exception as e:
        logger.error(f"Error querying links: {e}")
        return []

@app.get("/containers/")
def list_containers(db: Session = Depends(get_db)):
    try:
        return db.query(models.Container).order_by(models.Container.name).all()
    except Exception as e:
        logger.error(f"Error querying containers: {e}")
        return []

@app.get("/topology/")
def get_topology(db: Session = Depends(get_db)):
    try:
        hosts = db.query(models.DiscoveredHost).all()
        links = db.query(models.NetworkLink).all()
        containers = db.query(models.Container).filter(models.Container.state != "removed").all()

        nodes = [
            {
                "id": h.ip,
                "label": h.hostname or h.ip,
                "title": f"{h.ip}\n{h.vendor or 'Unknown vendor'}\n{h.os_guess or 'OS unknown'}",
                "status": h.status,
                "device_type": guess_device_type(h, GATEWAY_IP),
            }
            for h in hosts
        ]

        edges = [{"from": l.source_ip, "to": l.target_ip, "type": l.link_type} for l in links]

        for c in containers:
            node_id = f"container-{c.container_id}"
            nodes.append({
                "id": node_id,
                "label": c.name,
                "title": f"{c.name}\n{c.image}\n{c.state}",
                "status": "up" if c.state == "running" else "down",
                "device_type": "container",
            })

            if c.host_ip:
                edges.append({"from": node_id, "to": c.host_ip, "type": "container"})

        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        logger.error(f"Error generating topology: {e}")
        return {"nodes": [], "edges": []}

@app.get("/topology/view", response_class=HTMLResponse)
def topology_view():
    return (Path(__file__).parent / "topology.html").read_text(encoding="utf-8")
