"""DataUpdateCoordinator for Lumme Energia."""
from __future__ import annotations

import asyncio
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
            # Ensure auth once before parallel fetches so both don't race to authenticate
            await self.api._ensure_auth()

            # Fetch day and month consumption in parallel; contracts cached after first call
            (latest_date, latest_kwh), monthly_kwh, contracts, gsrn = await asyncio.gather(
                self.api.get_latest_day_consumption(),
                self.api.get_monthly_consumption_kwh(),
                self.api.get_contracts(),
                self.api.get_gsrn(),
            )
            address = ""
            if contracts:
                a = contracts[0].get("meteringpointAddress", {})
                parts = [
                    a.get("streetName", ""),
                    a.get("houseNumber", "") + a.get("houseLetter", ""),
                    a.get("cityName", ""),
                ]
                address = " ".join(p for p in parts if p).strip()
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
