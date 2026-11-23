"""
Thin wrapper around the Gophish REST API.

Designed to fail soft: if GOPHISH_API_KEY isn't set or Gophish isn't reachable,
every method logs a warning and returns None instead of raising, so the rest
of the platform (template generation, analytics, feedback) keeps working in a
standalone demo without a running Gophish instance.
"""
import logging
import os
import httpx

logger = logging.getLogger("gophish_client")

GOPHISH_BASE_URL = os.getenv("GOPHISH_BASE_URL", "https://localhost:3333")
GOPHISH_API_KEY = os.getenv("GOPHISH_API_KEY", "")
GOPHISH_VERIFY_SSL = os.getenv("GOPHISH_VERIFY_SSL", "false").lower() == "true"


class GophishClient:
    def __init__(self):
        self.enabled = bool(GOPHISH_API_KEY)
        self._client = httpx.Client(
            base_url=GOPHISH_BASE_URL,
            verify=GOPHISH_VERIFY_SSL,
            params={"api_key": GOPHISH_API_KEY} if GOPHISH_API_KEY else {},
            timeout=10,
        )

    def _request(self, method, path, **kwargs):
        if not self.enabled:
            logger.warning("Gophish disabled (no GOPHISH_API_KEY) — skipping %s %s", method, path)
            return None
        try:
            resp = self._client.request(method, path, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001 - deliberately broad for a soft-fail demo tool
            logger.warning("Gophish call failed (%s %s): %s", method, path, exc)
            return None

    def create_template(self, name: str, subject: str, html: str):
        payload = {"name": name, "subject": subject, "html": html}
        return self._request("POST", "/api/templates/", json=payload)

    def create_campaign(self, name: str, template_name: str, group_name: str,
                         page_name: str, smtp_name: str, url: str):
        payload = {
            "name": name,
            "template": {"name": template_name},
            "url": url,
            "page": {"name": page_name},
            "smtp": {"name": smtp_name},
            "groups": [{"name": group_name}],
        }
        return self._request("POST", "/api/campaigns/", json=payload)

    def get_campaign_results(self, campaign_id: int):
        return self._request("GET", f"/api/campaigns/{campaign_id}/results")


gophish_client = GophishClient()
