"""Config flow for SCAU Electricity."""

from __future__ import annotations

import logging
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
    CONF_RETRY_ATTEMPTS,
    CONF_RETRY_DELAY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_DELAY_SECONDS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ScauElectricityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle UI configuration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        description_placeholders = {"error": ""}
        if user_input is not None:
            room_id = str(user_input[CONF_ROOM_ID]).strip()
            room_name = str(user_input[CONF_ROOM_NAME]).strip()
            scan_interval = int(user_input[CONF_SCAN_INTERVAL])
            retry_attempts = int(user_input[CONF_RETRY_ATTEMPTS])
            retry_delay = int(user_input[CONF_RETRY_DELAY])
            await self.async_set_unique_id(room_id)
            self._abort_if_unique_id_configured()
            api = ScauElectricityApi(
                async_get_clientsession(self.hass), room_id, room_name
            )
            try:
                await api.async_get_data_with_retries(
                    dt_util.now().date(),
                    retry_attempts=retry_attempts,
                    retry_delay=retry_delay,
                )
            except ScauApiConnectionError as err:
                errors["base"] = "cannot_connect"
                description_placeholders["error"] = str(err)
                _LOGGER.error("验证房间失败: %s", err)
            except ScauApiError as err:
                errors["base"] = "invalid_room"
                description_placeholders["error"] = str(err)
                _LOGGER.error("验证房间失败: %s", err)
            else:
                return self.async_create_entry(
                    title=room_name,
                    data={
                        CONF_ROOM_ID: room_id,
                        CONF_ROOM_NAME: room_name,
                        CONF_SCAN_INTERVAL: scan_interval,
                        CONF_RETRY_ATTEMPTS: retry_attempts,
                        CONF_RETRY_DELAY: retry_delay,
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
                vol.Required(
                    CONF_RETRY_ATTEMPTS,
                    default=values.get(CONF_RETRY_ATTEMPTS, DEFAULT_RETRY_ATTEMPTS),
                ): vol.All(vol.Coerce(int), vol.Range(min=0)),
                vol.Required(
                    CONF_RETRY_DELAY,
                    default=values.get(CONF_RETRY_DELAY, DEFAULT_RETRY_DELAY_SECONDS),
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )
