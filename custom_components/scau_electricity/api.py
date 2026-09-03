"""Asynchronous client for the legacy SCAU electricity API."""

from __future__ import annotations

import hashlib
import json
import uuid
from asyncio import sleep
from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Any
from urllib.parse import parse_qsl, unquote

from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout

from .const import DEFAULT_BASE_URL, DEFAULT_DB_ID

COOKIE_NAME = "scauelectric"
REQUEST_TIMEOUT = ClientTimeout(total=35)


class ScauApiError(Exception):
    """Base SCAU API error."""


class ScauApiConnectionError(ScauApiError):
    """SCAU service connection error."""


class ScauApiResponseError(ScauApiError):
    """Invalid SCAU service response."""


@dataclass(frozen=True, slots=True)
class ScauSession:
    """Fields encoded in the login cookie."""

    token: str
    log_id: str
    timestamp: str


@dataclass(frozen=True, slots=True)
class ElectricityData:
    """Normalized readings for one room."""

    daily_energy: float
    total_energy: float
    balance_yuan: float
    balance_updated_at: str | None
    online: bool | None
    reading_date: date


def compact_json(value: object) -> str:
    """Serialize like JSON.stringify for signing."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def create_sign(token: str, request_data: object, timestamp: str) -> str:
    """Create the legacy request signature."""
    source = token + compact_json(request_data) + timestamp
    return hashlib.md5(source.encode("utf-8")).hexdigest()


class ScauElectricityApi:
    """Client for one electricity room."""

    def __init__(
        self,
        client: ClientSession,
        room_id: str,
        room_name: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        db_id: int = DEFAULT_DB_ID,
    ) -> None:
        self._client = client
        self._room_id = room_id
        self._room_name = room_name
        self._base_url = base_url.rstrip("/")
        self._db_id = db_id

    async def async_get_data(self, reading_date: date) -> ElectricityData:
        """Fetch readings, falling back to the previous meter day at zero."""
        data = await self._async_get_data_once(reading_date)
        if data.daily_energy != 0:
            return data

        previous = await self._async_get_data_once(reading_date - timedelta(days=1))
        return replace(data, daily_energy=previous.daily_energy)

    async def _async_get_data_once(self, reading_date: date) -> ElectricityData:
        """Fetch and normalize all readings."""
        day = reading_date.isoformat()
        usage_request = {
            "roomid": self._room_id,
            "roomname": self._room_name,
            # The endpoint returns no cumulative reading when the current day
            # has no detail row. Query its maximum 31-day window so the latest
            # historical row can provide the cumulative value.
            "starttime": (reading_date - timedelta(days=30)).isoformat(),
            "endtime": day,
        }
        balance_request = {"roomid": self._room_id, "roomname": self._room_name}
        usage_session = await self._async_login()
        usage = await self._async_post(
            "/api/zndb/getDBRYL", usage_request, usage_session
        )
        balance_session = await self._async_login()
        balance = await self._async_post(
            "/api/zndb/getDBYE", balance_request, balance_session
        )
        usage_data = self._mapping(usage.get("data"), "data")
        rows = usage_data.get("rows")
        if isinstance(rows, list) and rows:
            row_data = [
                self._mapping(row, f"data.rows[{index}]")
                for index, row in enumerate(rows)
            ]
            today_row = next(
                (row for row in row_data if row.get("date") == day), None
            )
            latest_row = max(
                row_data,
                key=lambda row: str(row.get("date", "")),
            )
            daily_energy = (
                self._number(today_row.get("ryl"), "ryl")
                if today_row is not None
                else 0.0
            )
            total_energy = self._number(latest_row.get("totryl"), "totryl")
        elif not rows:
            # The service returns no detail row for a day with no usage, but
            # still returns the cumulative reading at data.totryl.
            daily_energy = 0.0
            total_energy = self._number(usage_data.get("totryl"), "data.totryl")
        else:
            raise ScauApiResponseError("响应字段 data.rows 格式无效")
        balance_data = self._mapping(balance.get("data"), "data")
        return ElectricityData(
            daily_energy=daily_energy,
            total_energy=total_energy,
            balance_yuan=self._number(balance_data.get("dbye"), "dbye") / 100,
            balance_updated_at=self._string(balance_data.get("cbtime")),
            online=self._bool(balance_data.get("online")),
            reading_date=reading_date,
        )

    async def async_get_data_with_retries(
        self,
        reading_date: date,
        *,
        retry_attempts: int = 0,
        retry_delay: float = 0,
    ) -> ElectricityData:
        """Fetch readings, retrying failed requests before giving up."""
        for attempt in range(retry_attempts + 1):
            try:
                return await self.async_get_data(reading_date)
            except ScauApiError:
                if attempt >= retry_attempts:
                    raise
                await sleep(retry_delay)
        raise AssertionError("retry loop did not return or raise")

    async def _async_login(self) -> ScauSession:
        try:
            async with self._client.get(
                f"{self._base_url}/login",
                headers={
                    "Upgrade-Insecure-Requests": "1",
                    "X-Requested-With": "com.tencent.mm",
                },
                timeout=REQUEST_TIMEOUT,
            ) as response:
                await response.read()
                response.raise_for_status()
                cookie = response.cookies.get(COOKIE_NAME)
                if cookie is None:
                    for redirect in reversed(response.history):
                        if cookie := redirect.cookies.get(COOKIE_NAME):
                            break
        except ClientResponseError as err:
            raise ScauApiConnectionError(
                f"登录请求 HTTP {err.status}: {err.message or '无响应信息'}"
            ) from err
        except (ClientError, TimeoutError) as err:
            raise ScauApiConnectionError(f"无法连接华南农业大学电费服务: {err}") from err
        if cookie is None:
            raise ScauApiResponseError(f"登录响应缺少 {COOKIE_NAME} Cookie")
        fields = dict(parse_qsl(unquote(cookie.value), keep_blank_values=True))
        missing = {"token", "logid", "timestamp"} - fields.keys()
        if missing:
            raise ScauApiResponseError(
                f"登录 Cookie 缺少字段: {', '.join(sorted(missing))}"
            )
        try:
            uuid.UUID(fields["token"])
        except ValueError as err:
            raise ScauApiResponseError("登录 token 格式无效") from err
        if not fields["timestamp"].isdigit():
            raise ScauApiResponseError("登录 timestamp 格式无效")
        # aiohttp quotes this non-standard nested cookie because it contains
        # ampersands. The legacy endpoint only accepts its original raw form.
        self._client.cookie_jar.clear_domain("cz.scau.edu.cn")
        return ScauSession(fields["token"], fields["logid"], fields["timestamp"])

    async def _async_post(
        self, endpoint: str, request_data: dict[str, str], session: ScauSession
    ) -> dict[str, Any]:
        payload = {"url": endpoint, "request": request_data, "timeout": 30}
        cookie = (
            f"token={session.token}&logid={session.log_id}"
            f"&timestamp={session.timestamp}&method=home&dbid={self._db_id}"
        )
        try:
            async with self._client.post(
                f"{self._base_url}/getdata.ashx",
                data=compact_json(payload).encode("utf-8"),
                headers={
                    "sign": create_sign(session.token, request_data, session.timestamp),
                    "X-Requested-With": "XMLHttpRequest",
                    "Cookie": f"{COOKIE_NAME}={cookie}",
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                },
                timeout=REQUEST_TIMEOUT,
            ) as response:
                raw = await response.read()
                response.raise_for_status()
        except ClientResponseError as err:
            raise ScauApiConnectionError(
                f"读取数据 HTTP {err.status}: {err.message or '无响应信息'}"
            ) from err
        except (ClientError, TimeoutError) as err:
            raise ScauApiConnectionError(f"读取华南农业大学电费数据失败: {err}") from err
        try:
            result = json.loads(self._decode(raw))
        except json.JSONDecodeError as err:
            raise ScauApiResponseError("服务返回了无效 JSON") from err
        if not isinstance(result, dict):
            raise ScauApiResponseError("服务响应不是 JSON 对象")
        if result.get("code") not in (0, "0"):
            raise ScauApiResponseError(
                f"服务返回错误 code={result.get('code')}: "
                f"{result.get('msg') or '未知错误'}"
            )
        return result

    @staticmethod
    def _decode(raw: bytes) -> str:
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("gb18030", errors="replace")

    @staticmethod
    def _mapping(value: object, field: str) -> dict[str, Any]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as err:
                raise ScauApiResponseError(f"响应字段 {field} 格式无效") from err
        if not isinstance(value, dict):
            raise ScauApiResponseError(f"响应字段 {field} 格式无效")
        return value

    @staticmethod
    def _number(value: object, field: str) -> float:
        if not isinstance(value, int | float | str):
            raise ScauApiResponseError(f"响应字段 {field} 不是数值")
        try:
            return float(value)
        except (TypeError, ValueError) as err:
            raise ScauApiResponseError(f"响应字段 {field} 不是数值") from err

    @staticmethod
    def _string(value: object) -> str | None:
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _bool(value: object) -> bool | None:
        return bool(value) if value in (0, 1) else None
