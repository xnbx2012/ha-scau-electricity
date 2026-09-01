"""SCAU Electricity integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ScauElectricityApi
from .const import CONF_ROOM_ID, CONF_ROOM_NAME, DOMAIN, PLATFORMS
from .coordinator import ScauElectricityCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    api = ScauElectricityApi(
        async_get_clientsession(hass),
        entry.data[CONF_ROOM_ID],
        entry.data[CONF_ROOM_NAME],
    )
    coordinator = ScauElectricityCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
