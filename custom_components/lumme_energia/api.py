"""OmaLumme API client."""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta

import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from .const import API_BASE, AUTH_URL

_LOGGER = logging.getLogger(__name__)


class LummeAuthError(Exception):
    """Authentication failed."""


class LummeApiError(Exception):
    """API call failed."""


class LummeApi:
    def __init__(self, username: str, password: str, session: aiohttp.ClientSession) -> None:
        self._username = username
        self._password = password
        self._session = session
        self._token: str | None = None
        self._customer_id: int | None = None
        self._gsrn: str | None = None

    async def authenticate(self) -> None:
        ua = {"User-Agent": "Mozilla/5.0"}

        async with self._session.get(AUTH_URL, headers=ua) as resp:
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        form = soup.find("form")
        if not form:
            raise LummeAuthError("Login form not found")

        action = form["action"]
        inputs = {
            i.get("name"): i.get("value", "")
            for i in form.find_all("input")
            if i.get("name")
        }
        inputs["username"] = self._username
        inputs["password"] = self._password

        async with self._session.post(
            action, data=inputs, headers=ua, allow_redirects=False
        ) as resp:
            location = resp.headers.get("Location", "")

        if "code=" not in location:
            raise LummeAuthError("Login failed — check credentials")

        code = parse_qs(urlparse(location).query).get("code", [None])[0]
        if not code:
            raise LummeAuthError("Authorization code not found")

        async with self._session.get(
            f"{API_BASE}/v1/oidcAuthorization/",
            headers={**ua, "code": code, "iframe": "false", "x-omalumme-version": "web"},
        ) as resp:
            if resp.status != 200:
                raise LummeAuthError(f"Token exchange failed: {resp.status}")
            data = json.loads(await resp.text())

        self._token = data.get("token")
        self._customer_id = data.get("customerId")
        if not self._token or not self._customer_id:
            raise LummeAuthError("No token in auth response")

        _LOGGER.debug("Authenticated as customerId=%s", self._customer_id)

    async def _ensure_auth(self) -> None:
        if not self._token:
            await self.authenticate()

    def _api_headers(self) -> dict:
        bearer = (self._token or "")[:5000]
        return {
            "Authorization": f"Bearer {bearer}",
            "x-omalumme-version": "web",
            "Content-Type": "application/json",
        }

    def _api_body(self) -> dict:
        content = (self._token or "")[5000:]
        return {"content": content}

    async def get_contracts(self) -> list[dict]:
        await self._ensure_auth()
        cid = self._customer_id
        async with self._session.get(
            f"{API_BASE}/v1/contractBasicData/{cid}",
            headers=self._api_headers(),
        ) as resp:
            if resp.status == 401:
                self._token = None
                raise LummeAuthError("Token expired")
            if resp.status != 200:
                raise LummeApiError(f"contractBasicData failed: {resp.status}")
            return json.loads(await resp.text())

    async def get_gsrn(self) -> str:
        if self._gsrn:
            return self._gsrn
        contracts = await self.get_contracts()
        if not contracts:
            raise LummeApiError("No contracts found")
        gsrn = contracts[0].get("GSRN")
        if not gsrn:
            raise LummeApiError("GSRN not found in contract")
        self._gsrn = gsrn
        return gsrn

    async def get_consumption(
        self,
        start: date,
        end: date,
        view_period: str = "hour",
    ) -> list[dict]:
        """Fetch consumption data.
        view_period: 'hour' = 15-min slots, 'day' = hourly slots.
        Returns list of {startTime, endTime, sum, costWithVat}.
        Data has ~1-day lag; today's data is typically not yet available.
        """
        await self._ensure_auth()
        gsrn = await self.get_gsrn()
        cid = self._customer_id

        url = (
            f"{API_BASE}/v1/consumption/{cid}/{cid}/{gsrn}"
            f"?version=2&start={start.isoformat()}&end={end.isoformat()}&viewPeriod={view_period}"
        )
        async with self._session.post(
            url, headers=self._api_headers(), json=self._api_body()
        ) as resp:
            if resp.status == 401:
                self._token = None
                raise LummeAuthError("Token expired")
            if resp.status != 200:
                raise LummeApiError(f"consumption failed: {resp.status}")
            data = json.loads(await resp.text())

        return data.get("items", []) if isinstance(data, dict) else []

    async def get_latest_day_consumption(self) -> tuple[date, float]:
        """Return (date, kWh) for the most recent day with data."""
        today = date.today()
        for delta in range(3):
            d = today - timedelta(days=delta)
            items = await self.get_consumption(d, d, "hour")
            if items:
                total = round(sum(i.get("sum", 0) for i in items), 4)
                return d, total
        return today - timedelta(days=1), 0.0

    async def get_monthly_consumption_kwh(self) -> float:
        """Current calendar month's total kWh."""
        today = date.today()
        month_start = today.replace(day=1)
        end = today - timedelta(days=1)  # use latest complete day
        if end < month_start:
            return 0.0
        items = await self.get_consumption(month_start, end, "day")
        return round(sum(i.get("sum", 0) for i in items), 4)
