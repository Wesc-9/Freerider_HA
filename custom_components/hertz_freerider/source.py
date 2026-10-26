"""Rate-conscious shared public source feeds for all searches in one HA server.

No public permission to use these feeds at a particular frequency has been
established. Cache each country's response locally; never fan out a request
per saved watch. Respect Retry-After and back off after source errors.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import logging
from time import monotonic

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .filters import Ride, parse_transport_routes

_LOGGER = logging.getLogger(__name__)
MIN_CACHE_SECONDS = 900  # one source request per country per 15 minutes
MANUAL_MIN_SECONDS = 60  # avoid a refresh-button request storm
MAX_BACKOFF_SECONDS = 4 * 3600
ROUTE_API = {
    "NO": ("https://hertzfreerider.no/api/transport-routes/?country=NORWAY",
           "https://hertzfreerider.no/no-no/"),
    "SE": ("https://hertzfreerider.se/api/transport-routes/?country=SWEDEN",
           "https://hertzfreerider.se/sv-se/"),
}


class SourceNotReady(Exception):
    """A country feed has no verified usable source or was rate-limited."""


def retry_after_seconds(value: str | None) -> int | None:
    """Parse a Retry-After seconds value or HTTP date, clamped to 4 hours."""
    if not value:
        return None
    try:
        seconds = float(value)
    except (ValueError, TypeError):
        try:
            when = parsedate_to_datetime(value)
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            seconds = (when - datetime.now(timezone.utc)).total_seconds()
        except (ValueError, TypeError, OverflowError):
            return None
    return min(MAX_BACKOFF_SECONDS, max(0, int(seconds)))


class CountryFeed:
    """A single shared lock, bounded cache and backoff per provider country."""

    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.items: list[Ride] | None = None
        self.last_attempt = 0.0
        self.last_success = 0.0
        self.blocked_until = 0.0
        self.errors = 0
        self.etag: str | None = None
        self.modified: str | None = None

    async def get(self, hass, country: str, *, force: bool = False) -> list[Ride]:
        """Return a fresh-enough shared snapshot without duplicate requests."""
        async with self.lock:
            now = monotonic()
            age = now - self.last_success
            if self.items is not None and age < MIN_CACHE_SECONDS and (
                not force or now - self.last_attempt < MANUAL_MIN_SECONDS
            ):
                return list(self.items)
            if now < self.blocked_until:
                raise SourceNotReady(
                    f"{country}: provider backoff active, retry in "
                    f"{int(self.blocked_until - now)}s"
                )
            if now - self.last_attempt < MANUAL_MIN_SECONDS:
                if self.items is not None and age < MIN_CACHE_SECONDS:
                    return list(self.items)
                # Avoid hammering the provider on rapidly repeated failures.
                raise SourceNotReady(f"{country}: request cooldown active")
            self.last_attempt = now
            endpoint, homepage = ROUTE_API[country]
            headers = {"Accept": "application/json"}
            if self.etag:
                headers["If-None-Match"] = self.etag
            if self.modified:
                headers["If-Modified-Since"] = self.modified
            try:
                session = async_get_clientsession(hass)
                async with session.get(
                    endpoint, headers=headers, timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    if response.status == 304 and self.items is not None:
                        self.last_success = monotonic()
                        self.errors = 0
                        return list(self.items)
                    if response.status in (403, 429, 503):
                        self._failure(retry_after_seconds(response.headers.get("Retry-After")))
                        raise SourceNotReady(
                            f"{country}: provider returned HTTP {response.status}, backing off"
                        )
                    response.raise_for_status()
                    payload = await response.json(content_type=None)
                    parsed = parse_transport_routes(payload, country, homepage)
                    etag = response.headers.get("ETag")
                    modified = response.headers.get("Last-Modified")
            except SourceNotReady:
                raise
            except (aiohttp.ClientError, TimeoutError, ValueError, TypeError, KeyError) as exc:
                self._failure(None)
                raise SourceNotReady(f"{country}: source unavailable: {exc}") from exc

            self.items = parsed
            self.last_success = monotonic()
            self.errors = 0
            self.blocked_until = 0
            self.etag = etag
            self.modified = modified
            return list(parsed)

    def _failure(self, retry: int | None) -> None:
        self.errors += 1
        delay = retry if retry is not None else min(
            MAX_BACKOFF_SECONDS, 60 * (2 ** min(self.errors, 6))
        )
        self.blocked_until = monotonic() + max(60, delay)


async def async_fetch_country(hass, country: str, *, force: bool = False) -> list[Ride]:
    """Shared per-installation feed and protection, regardless of watch count."""
    if country not in ROUTE_API:
        raise SourceNotReady(f"{country}: no verified listing adapter")
    feeds = hass.data.setdefault(f"{DOMAIN}_shared_country_feeds", {})
    feed = feeds.setdefault(country, CountryFeed())
    return await feed.get(hass, country, force=force)
