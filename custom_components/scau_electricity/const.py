"""Constants for the SCAU Electricity integration."""

from typing import Final

DOMAIN: Final = "scau_electricity"
PLATFORMS: Final = ["sensor"]
CONF_ROOM_ID: Final = "room_id"
CONF_ROOM_NAME: Final = "room_name"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_RETRY_ATTEMPTS: Final = "retry_attempts"
CONF_RETRY_DELAY: Final = "retry_delay"
CONF_ELECTRICITY_PRICE: Final = "electricity_price"
DEFAULT_BASE_URL: Final = "http://cz.scau.edu.cn"
DEFAULT_DB_ID: Final = 9853
DEFAULT_SCAN_INTERVAL_MINUTES: Final = 60
DEFAULT_RETRY_ATTEMPTS: Final = 5
DEFAULT_RETRY_DELAY_SECONDS: Final = 10
DEFAULT_ELECTRICITY_PRICE_YUAN_PER_KWH: Final = 0.6259
