from datetime import datetime, timedelta
import pytz


def get_today_unix():
    tz = pytz.timezone("Etc/GMT-7")
    now = datetime.now(tz)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_unix = int(today.timestamp())
    return today_unix


def get_tomorrow_unix():
    tz = pytz.timezone("Etc/GMT-7")
    now = datetime.now(tz)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    tomorrow_unix = int(tomorrow.timestamp())
    return tomorrow_unix


def toObject(self, data):
    lines = data.split("\n")
    result = {}
    for line in lines:
        if not line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if value.isdigit():
            value = int(value)
        elif not value:
            value = None
        if "[" in key:
            key, sub_key = key.split(".")
            index = int(key[key.index("[") + 1 : key.index("]")])
            key = key[: key.index("[")]
            if key not in result:
                result[key] = []
            if len(result[key]) <= index:
                result[key].append({})
            result[key][index][sub_key] = value
        else:
            result[key] = value
    return result
