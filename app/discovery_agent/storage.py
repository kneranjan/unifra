from sqlalchemy import func
from app.database import SessionLocal
from app import models
from app.discovery_agent.scan import discover_hosts , scan_ports
from app.discovery_agent.docker_scan import discover_containers
import time


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



def mark_down_hosts(seen_ips):
  db = SessionLocal()
  count = 0
  #get all hosts that are marked "up" in the db
  up_hosts = db.query(models.DiscoveredHost).filter(models.DiscoveredHost.status=="up").all()

  for host in up_hosts:
    if host.ip not in seen_ips:
      host.status = "down"
      count += 1
    
  db.commit()
  db.close()
  return count

def save_links(gateway_ip):
  db = SessionLocal()
  count = 0

  up_hosts = db.query(models.DiscoveredHost).filter(models.DiscoveredHost.status == "up").all()

  for host in up_hosts:
    #skip the gateway
    if host.ip == gateway_ip:
      continue

    #check for existing n/w links
    existing = db.query(models.NetworkLink).filter(models.NetworkLink.source_ip == host.ip).filter(models.NetworkLink.target_ip == gateway_ip).first()

    if existing:
      existing.last_seen = func.now()
    else:
      db.add(models.NetworkLink(source_ip = host.ip, target_ip = gateway_ip))
      count+=1

  db.commit()
  db.close()
  return count        



def save_containers(containers):
  db = SessionLocal()
  new = 0
  updated = 0

  for c in containers:
    existing = db.query(models.Container).filter(models.Container.container_id == c["container_id"]).first()

    if existing:
      existing.state = c["state"]
      existing.name = c["name"]
      existing.image = c["image"]
      existing.last_seen = func.now()
      updated+=1
    else:
      db.add(models.Container(
          container_id = c["container_id"],
          name = c["name"],
          image = c["image"],
          state = c["state"],
      ))
      new+=1

  db.commit()
  db.close()
  return new,updated  


def run_scan():
  containers = discover_containers()
  new,updated = save_containers(containers)
  print(f"Containers saved: {new} new , {updated} updated")
  hosts = discover_hosts("192.168.1.0/24")
  new,updated = save_hosts(hosts)
  print(f"Scan Saved: {new} new, {updated} updated")

  seen_ips = [h["ip"] for h in hosts]
  down = mark_down_hosts(seen_ips)
  print(f"Marked down: {down}")

  scanned = update_ports()
  print(f"Ports updated for {scanned} hosts")

  links = save_links("192.168.1.1")
  print(f"New links saved : {links}")



if __name__ == "__main__":
  

  SCAN_INTERVAL = 300 #5 mins = 300 sec
  while True:
    run_scan()
    print(f"unifri is sleeping for {SCAN_INTERVAL} seconds")
    time.sleep(SCAN_INTERVAL)