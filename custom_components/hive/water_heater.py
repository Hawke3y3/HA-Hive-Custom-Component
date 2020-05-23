"""Support for hive water heaters."""

from homeassistant.components.water_heater import (
    STATE_ECO,
    STATE_OFF,
    STATE_ON,
    SUPPORT_OPERATION_MODE,
    WaterHeaterDevice,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS, TEMP_FAHRENHEIT
from homeassistant.helpers import aiohttp_client

from . import DOMAIN, HiveEntity, refresh_system

SUPPORT_FLAGS_HEATER = SUPPORT_OPERATION_MODE

HIVE_TO_HASS_STATE = {
    "SCHEDULE": STATE_ECO,
    "ON": STATE_ON,
    "OFF": STATE_OFF,
}

HASS_TO_HIVE_STATE = {
    STATE_ECO: "SCHEDULE",
    STATE_ON: "ON",
    STATE_OFF: "OFF",
}

SUPPORT_WATER_HEATER = [STATE_ECO, STATE_ON, STATE_OFF]


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Hive Hotwater.

    No longer in use.
    """


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Hive Hotwater based on a config entry."""
    from pyhiveapi import Hotwater

    session = aiohttp_client.async_get_clientsession(hass)
    hive = hass.data[DOMAIN][entry.entry_id]
    hive.hotwater = Hotwater(session)
    devices = hive.devices.get("water_heater")
    if devices:
        devs = []
        for dev in devices:
            devs.append(HiveWaterHeater(hive, dev))
    async_add_entities(devs, True)


class HiveWaterHeater(HiveEntity, WaterHeaterDevice):
    """Hive Water Heater Device."""

    @property
    def unique_id(self):
        """Return unique ID of entity."""
        return self._unique_id

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.device["hive_id"])},
            "name": self.device["hive_name"],
            "model": self.device["device_data"]["model"],
            "manufacturer": self.device["device_data"]["manufacturer"],
            "sw_version": self.device["device_data"]["version"],
            "via_device": (DOMAIN, self.device["parent_device"]),
            "battery": self.device["device_data"]["battery"]
        }

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS_HEATER

    @property
    def name(self):
        """Return the name of the water heater."""
        return self.device.get("ha_name", "Hot Water")

    @property
    def available(self):
        """Return if the device is availble"""
        return self.attributes["available"]

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_operation(self):
        """ Return current operation. """
        return HIVE_TO_HASS_STATE[self.device["current_operation"]]

    @property
    def operation_list(self):
        """List of available operation modes."""
        return SUPPORT_WATER_HEATER

    @refresh_system
    async def async_set_operation_mode(self, operation_mode):
        """Set operation mode."""
        new_mode = HASS_TO_HIVE_STATE[operation_mode]
        await self.hive.hotwater.set_mode(self.device, new_mode)

    async def async_update(self):
        """Update all Node data from Hive."""
        await self.hive.session.update_data(self.device)
        self.device = await self.hive.howater.get_hotwater(self.device)
        self.attributes.update(self.device.get("attributes", {}))
