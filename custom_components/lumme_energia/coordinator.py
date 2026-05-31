"""DataUpdateCoordinator for Lumme Energia."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LummeApi, LummeAuthError, LummeApiError
from .const import DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class LummeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api: LummeApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.api = api

    async def _async_update_data(self) -> dict:
        try:
            latest_date, latest_kwh = await self.api.get_latest_day_consumption()
            monthly_kwh = await self.api.get_monthly_consumption_kwh()
            contracts = await self.api.get_contracts()
            address = ""
            if contracts:
                a = contracts[0].get("meteringpointAddress", {})
                parts = [
                    a.get("streetName", ""),
                    a.get("houseNumber", "") + a.get("houseLetter", ""),
                    a.get("cityName", ""),
                ]
                address = " ".join(p for p in parts if p).strip()
            gsrn = await self.api.get_gsrn()
            return {
                "latest_date": latest_date.isoformat(),
                "latest_kwh": latest_kwh,
                "monthly_kwh": monthly_kwh,
                "address": address,
                "gsrn": gsrn,
            }
        except LummeAuthError as err:
            _LOGGER.warning("Auth error, re-authenticating next cycle: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except LummeApiError as err:
            raise UpdateFailed(f"API error: {err}") from err
