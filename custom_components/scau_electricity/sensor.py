"""Sensors for SCAU Electricity."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ElectricityData
from .const import CONF_ROOM_ID, CONF_ROOM_NAME, DOMAIN
from .coordinator import ScauElectricityCoordinator


@dataclass(frozen=True, kw_only=True)
class ScauSensorDescription(SensorEntityDescription):
    """Describe a sensor and its coordinator value."""

    value_fn: Callable[[ElectricityData], float]


SENSORS = (
    ScauSensorDescription(
        key="daily_energy",
        translation_key="daily_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda data: data.daily_energy,
    ),
    ScauSensorDescription(
        key="total_energy",
        translation_key="total_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        value_fn=lambda data: data.total_energy,
    ),
    ScauSensorDescription(
        key="balance",
        translation_key="balance",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="CNY",
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda data: data.balance_yuan,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator: ScauElectricityCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ScauElectricitySensor(coordinator, entry, item) for item in SENSORS
    )


class ScauElectricitySensor(
    CoordinatorEntity[ScauElectricityCoordinator], SensorEntity
):
    """An electricity reading."""

    entity_description: ScauSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ScauElectricityCoordinator,
        entry: ConfigEntry,
        description: ScauSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        room_id = entry.data[CONF_ROOM_ID]
        self._attr_unique_id = f"{room_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, room_id)},
            name=entry.data[CONF_ROOM_NAME],
            manufacturer="华南农业大学",
            model="宿舍智能电表",
        )

    @property
    def native_value(self) -> float:
        """Return the native sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, str | bool] | None:
        """Return balance metadata."""
        if self.entity_description.key != "balance":
            return None
        attributes: dict[str, str | bool] = {}
        if self.coordinator.data.balance_updated_at is not None:
            attributes["balance_updated_at"] = self.coordinator.data.balance_updated_at
        if self.coordinator.data.online is not None:
            attributes["online"] = self.coordinator.data.online
        return attributes
