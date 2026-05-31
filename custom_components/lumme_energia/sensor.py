"""Lumme Energia sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LummeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LummeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        LummeLatestDaySensor(coordinator, entry),
        LummeMonthlySensor(coordinator, entry),
    ])


class LummeBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: LummeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data or {}
        address = data.get("address", "Lumme Energia")
        gsrn = data.get("gsrn")
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Lumme Energia – {address}" if address else "Lumme Energia",
            manufacturer="Lumme Energia",
            model="Sähkömittari",
            configuration_url="https://oma.lumme-energia.fi/",
            serial_number=gsrn or None,
        )


class LummeLatestDaySensor(LummeBaseSensor):
    """Yesterday's (or most recent available) daily consumption."""
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:lightning-bolt"

    def __init__(self, coordinator: LummeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_daily"
        self._attr_name = "Päivän kulutus"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        return data.get("latest_kwh")

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        return {
            "data_date": data.get("latest_date"),
            "note": "Data is typically 1 day delayed",
        }


class LummeMonthlySensor(LummeBaseSensor):
    """Current calendar month's cumulative consumption."""
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:lightning-bolt-circle"

    def __init__(self, coordinator: LummeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_monthly"
        self._attr_name = "Kuukauden kulutus"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        return data.get("monthly_kwh")

    @property
    def extra_state_attributes(self) -> dict:
        return {"period": "current_month"}
