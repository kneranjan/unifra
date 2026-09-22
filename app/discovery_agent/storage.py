from sqlalchemy import func
from app.database import SessionLocal
from app import models
from app.discovery_agent.scan import discover_hosts , scan_ports


def save_hosts(hosts):
  db = SessionLocal()
  new_count = 0
  updated_count = 0
  try:
    for h in hosts:
      existing = (
        db.query(models.DiscoveredHost)
        .filter(models.DiscoveredHost.ip == h["ip"])
        .first()
      )

      if existing:
        # Seen before: refresh it instead of adding a duplicate
        existing.status = h["status"]
        existing.last_seen = func.now()
        if h["mac"] is not None:
          existing.mac = h["mac"]
          existing.vendor = h["vendor"]
        if h["hostname"] is not None:
          existing.hostname = h["hostname"]
        updated_count += 1
      else:
        # Never seen: insert a new row
        db.add(models.DiscoveredHost(
          ip=h["ip"],
          mac=h["mac"],
          vendor=h["vendor"],
          status=h["status"],
          hostname = h["hostname"],
        ))
        new_count += 1

    db.commit()
  finally:
    db.close()

  return new_count, updated_count

def update_ports():
  db = SessionLocal()
  scanned = 0
  try:
    hosts = (
      db.query(models.DiscoveredHost)
      .filter(models.DiscoveredHost.status == "up")
      .all()
    )

    for host in hosts:
      try:
        result = scan_ports(host.ip)
      except Exception as e:
        print(f"Port scan failed for {host.ip}: {e}")
        continue

      host.open_ports = result["open_ports"]
      host.os_guess = result["os_guess"]
      db.commit()
      scanned += 1
      print(f"{host.ip}: {len(result['open_ports'])} open ports")
  finally:
    db.close()

  return scanned


if __name__ == "__main__":
  hosts = discover_hosts("192.168.1.0/24")
  new, updated = save_hosts(hosts)
  print(f"Scan saved: {new} new, {updated} updated")

  scanned = update_ports()
  print(f"Ports updated for {scanned} hosts")