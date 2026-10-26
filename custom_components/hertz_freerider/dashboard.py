"""Register an optional Freerider HA results card for Lovelace dashboards.

Failure to register a presentation-only resource must never break route
monitoring or alerts. In YAML dashboard mode, owners manually add the resource.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import CoreState, EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)

RESOURCE_BASE = "/freerider-ha"
RESOURCE_PATH = f"{RESOURCE_BASE}/freerider-rides-card.js"
VERSION = "0.9.0"


async def async_setup_dashboard(hass) -> None:
    """Expose the card module and register in storage-mode Lovelace once."""
    path = Path(__file__).parent / "frontend"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(RESOURCE_BASE, str(path), False)]
        )
    except RuntimeError:
        _LOGGER.debug("Freerider dashboard static path already registered")
    except Exception:
        _LOGGER.exception("Could not expose Freerider dashboard card")
        return

    async def _register_resource(_event=None, attempt=0) -> None:
        try:
            lovelace = hass.data.get("lovelace")
            if lovelace is None or getattr(lovelace, "mode", None) != "storage":
                _LOGGER.debug("Freerider card resource can be added manually in YAML mode")
                return
            resources = getattr(lovelace, "resources", None)
            if resources is None:
                return
            if not getattr(resources, "loaded", False):
                if attempt < 12:
                    async_call_later(
                        hass, 5,
                        lambda _now: hass.async_create_task(
                            _register_resource(attempt=attempt + 1)
                        ),
                    )
                return
            resource_url = f"{RESOURCE_PATH}?v={VERSION}"
            for resource in resources.async_items():
                url = resource.get("url", "")
                if url.split("?")[0] == RESOURCE_PATH:
                    if url != resource_url:
                        await resources.async_update_item(
                            resource["id"],
                            {"url": resource_url, "res_type": "module"},
                        )
                    return
            await resources.async_create_item({
                "url": resource_url,
                "res_type": "module",
            })
            _LOGGER.info("Registered optional Freerider HA dashboard card")
        except Exception:
            _LOGGER.exception("Could not auto-register Freerider Lovelace resource")

    if hass.state == CoreState.running:
        await _register_resource()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _register_resource)
