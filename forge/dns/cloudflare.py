from __future__ import annotations

import httpx

from forge.github.errors import GitHubError


class CloudflareError(Exception):
    pass


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def get_zone_id(token: str, domain: str) -> str:
    """Get the Cloudflare zone ID for a domain (supports subdomains)."""
    # Try progressively shorter suffixes to find the zone
    parts = domain.split(".")
    for i in range(len(parts) - 1):
        candidate = ".".join(parts[i:])
        resp = httpx.get(
            "https://api.cloudflare.com/client/v4/zones",
            headers=_headers(token),
            params={"name": candidate},
        )
        data = resp.json()
        if data.get("success") and data["result"]:
            return data["result"][0]["id"]
    raise CloudflareError(f"No Cloudflare zone found for '{domain}'. Make sure the domain is added to your Cloudflare account.")


def create_a_record(token: str, domain: str, ip: str) -> None:
    """Create an A record pointing domain to ip."""
    zone_id = get_zone_id(token, domain)

    # Check if record already exists
    resp = httpx.get(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
        headers=_headers(token),
        params={"type": "A", "name": domain},
    )
    existing = resp.json().get("result", [])
    if existing:
        # Update existing record
        record_id = existing[0]["id"]
        resp = httpx.put(
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}",
            headers=_headers(token),
            json={"type": "A", "name": domain, "content": ip, "ttl": 1, "proxied": False},
        )
    else:
        resp = httpx.post(
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
            headers=_headers(token),
            json={"type": "A", "name": domain, "content": ip, "ttl": 1, "proxied": False},
        )

    data = resp.json()
    if not data.get("success"):
        errors = data.get("errors", [])
        raise CloudflareError(f"Failed to create DNS record: {errors}")
