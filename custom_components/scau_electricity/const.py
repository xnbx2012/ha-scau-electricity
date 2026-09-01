"""Constants for the SCAU Electricity integration."""

from typing import Final

DOMAIN: Final = "scau_electricity"
PLATFORMS: Final = ["sensor"]
CONF_ROOM_ID: Final = "room_id"
CONF_ROOM_NAME: Final = "room_name"
CONF_SCAN_INTERVAL: Final = "scan_interval"
DEFAULT_BASE_URL: Final = "http://cz.scau.edu.cn"
DEFAULT_DB_ID: Final = 9853
DEFAULT_SCAN_INTERVAL_MINUTES: Final = 60
ELECTRICITY_PRICE_YUAN_PER_KWH: Final = 0.63
