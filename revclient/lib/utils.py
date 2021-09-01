import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import RevClient

MAX_INT = (2**31 - 1)

#%%
iso_re = re.compile('([\d:T-]+\.\d\d\d)\d*(\+\d+:\d+|Z)?')

def parse_iso(val):
    cleaned = iso_re.match(val)
    return datetime.fromisoformat((cleaned[1] + '+00:00') if cleaned else val)

def format_iso(val):
    return val.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def now_iso():
    return datetime.now(timezone.utc)

def coerce_iso(val):
    if isinstance(val, datetime):
        return val
    

def omit(items, omit_keys, asItems=False):
    if isinstance(items, dict):
        items = items.items()
    result = [ var for var in items if var[0] not in omit_keys ]
    if asItems:
        return result
    else:
        return dict(result)



class NamespacedClient(object):
    def __init__(self, client: 'RevClient'):
        self.client = client
