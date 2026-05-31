"""Config flow for Lumme Energia."""
from __future__ import annotations

import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .api import LummeApi, LummeAuthError
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD

STEP_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
})


async def _validate_credentials(hass: HomeAssistant, username: str, password: str) -> None:
    session = aiohttp.ClientSession()
    try:
        api = LummeApi(username, password, session)
        await api.authenticate()
        await api.get_contracts()
    finally:
        await session.close()


class LummeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                await _validate_credentials(
                    self.hass,
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                return self.async_create_entry(
                    title=f"Lumme Energia ({user_input[CONF_USERNAME]})",
                    data=user_input,
                )
            except LummeAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_SCHEMA,
            errors=errors,
        )
