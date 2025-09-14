from datetime import datetime
from zoneinfo import ZoneInfo
from config import CFG

TZ = ZoneInfo(CFG["TZ"])

def now_local():
    return datetime.now(TZ)
