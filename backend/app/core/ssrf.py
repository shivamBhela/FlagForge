import socket
import ipaddress
from urllib.parse import urlparse
from fastapi import HTTPException, status


class SSRFValidationError(ValueError):
    """Raised when a URL targets a prohibited or internal destination."""
    pass


def validate_target_url(url: str, allow_local_network: bool = False) -> str:
    """Validates that a URL uses safe HTTP/HTTPS schemes and does not point
    to internal, loopback, link-local, or cloud metadata addresses.
    """
    if not url:
        raise SSRFValidationError("URL cannot be empty")

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFValidationError(f"Invalid URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("URL does not contain a valid hostname.")

    # Check for localhost / loopback aliases directly
    lower_host = hostname.lower()
    if not allow_local_network:
        if lower_host in ("localhost", "127.0.0.1", "::1", "metadata.google.internal", "instance-data"):
            raise SSRFValidationError(f"Access to '{hostname}' is prohibited (loopback/metadata protection).")

    # Resolve IP addresses
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as e:
        raise SSRFValidationError(f"Could not resolve hostname '{hostname}': {str(e)}")

    for item in addr_info:
        ip_str = item[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if not allow_local_network:
            # Explicit AWS/GCP/Azure link-local metadata address check
            if ip_str == "169.254.169.254":
                raise SSRFValidationError("Access to cloud metadata endpoints (169.254.169.254) is strictly blocked.")
            if ip.is_loopback:
                raise SSRFValidationError(f"IP {ip} is a loopback address and cannot be accessed.")
            if ip.is_link_local:
                raise SSRFValidationError(f"IP {ip} is a link-local address (metadata defense) and cannot be accessed.")
            if ip.is_private:
                raise SSRFValidationError(f"IP {ip} is in a private network range and cannot be accessed.")
            if ip.is_multicast or ip.is_reserved:
                raise SSRFValidationError(f"IP {ip} is reserved/multicast and cannot be accessed.")

    return url
