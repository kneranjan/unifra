def guess_device_type(host, gateway_ip):
  port_nums = [p["port"] for p in (host.open_ports or [])]
  vendor = (host.vendor or "").lower()
  os_guess = (host.os_guess or "").lower()

  if host.ip == gateway_ip:
    return "router"

  if any(p in port_nums for p in [22, 80, 443, 5432]):
    return "server"

  if any(brand in vendor for brand in ["apple", "samsung", "xiaomi"]):
    return "phone"

  if "windows" in os_guess:
    return "pc"

  return "unknown"