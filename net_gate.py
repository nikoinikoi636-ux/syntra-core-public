from urllib.parse import urlsplit
import ipaddress, requests

ALLOWED = {"httpbin.org", "raw.githubusercontent.com"}

def _host_allowed(host: str) -> bool:
    # Блокирай голи IP-та освен ако не са в ALLOWED
    try:
        ipaddress.ip_address(host)
        return host in ALLOWED
    except ValueError:
        pass
    # разреши поддомейни на позволените
    return host in ALLOWED or any(host.endswith("."+d) for d in ALLOWED)

def safe_get(url: str, **kw):
    host = urlsplit(url).hostname or ""
    if not _host_allowed(host):
        raise ValueError(f"blocked: domain '{host}' not allowed")
    kw.setdefault("timeout", 10)
    return requests.get(url, **kw)
