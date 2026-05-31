"""Lumme Energia integration."""
from __future__ import annotations

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import LummeApi
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD
from .coordinator import LummeCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = aiohttp.ClientSession()
    api = LummeApi(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], session)

    coordinator = LummeCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: LummeCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api._session.close()
    return unload_ok
