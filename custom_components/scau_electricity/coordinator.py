"""Data coordinator for SCAU Electricity."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import ElectricityData, ScauApiError, ScauElectricityApi
from .const import DEFAULT_SCAN_INTERVAL_MINUTES, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ScauElectricityCoordinator(DataUpdateCoordinator[ElectricityData]):
    """Coordinate polling for one room."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: ScauElectricityApi
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
            config_entry=entry,
        )
        self.api = api

    async def _async_update_data(self) -> ElectricityData:
        try:
            return await self.api.async_get_data(dt_util.now().date())
        except ScauApiError as err:
            raise UpdateFailed(str(err)) from err
