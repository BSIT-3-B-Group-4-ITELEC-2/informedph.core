from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

PH_TIMEZONE = ZoneInfo("Asia/Manila")

def normalize_date(value):
    if not value:
        return None

    value = value.strip()

    try:
        dt = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        try:
            dt = parsedate_to_datetime(value)
        except (ValueError, TypeError, OverflowError):
            return None

    if dt.tzinfo is None:
        return None

    return dt.astimezone(PH_TIMEZONE).isoformat()