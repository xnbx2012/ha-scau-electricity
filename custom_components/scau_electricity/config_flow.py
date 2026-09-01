"""Config flow for SCAU Electricity."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .api import ScauApiConnectionError, ScauApiError, ScauElectricityApi
from .const import (
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)


class ScauElectricityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle UI configuration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            room_id = str(user_input[CONF_ROOM_ID]).strip()
            room_name = str(user_input[CONF_ROOM_NAME]).strip()
            scan_interval = int(user_input[CONF_SCAN_INTERVAL])
            await self.async_set_unique_id(room_id)
            self._abort_if_unique_id_configured()
            api = ScauElectricityApi(
                async_get_clientsession(self.hass), room_id, room_name
            )
            try:
                await api.async_get_data(dt_util.now().date())
            except ScauApiConnectionError:
                errors["base"] = "cannot_connect"
            except ScauApiError:
                errors["base"] = "invalid_room"
            else:
                return self.async_create_entry(
                    title=room_name,
                    data={
                        CONF_ROOM_ID: room_id,
                        CONF_ROOM_NAME: room_name,
                        CONF_SCAN_INTERVAL: scan_interval,
                    },
                )
        values = user_input or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ROOM_NAME, default=values.get(CONF_ROOM_NAME, "")
                ): str,
                vol.Required(CONF_ROOM_ID, default=values.get(CONF_ROOM_ID, "")): str,
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=values.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
