# app/utils/timezone.py

import os
from datetime import time
from zoneinfo import ZoneInfo

TIMEZONE_ENV_VAR = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
IST = ZoneInfo(TIMEZONE_ENV_VAR)
