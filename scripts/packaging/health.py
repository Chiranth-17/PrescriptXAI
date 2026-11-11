"""Check a local HTTPS listener without bypassing its authentication boundary."""

import os
import ssl
import urllib.error
import urllib.request

context = ssl.create_default_context(cafile=os.environ.get("PRESCRIPTXAI_TLS_CERTFILE"))
url = os.environ.get("PSX_HEALTH_URL", "https://localhost:8000/auth/session")
try:
    with urllib.request.urlopen(url, context=context, timeout=8) as response:
        if response.status != 200:
            raise SystemExit(1)
except urllib.error.HTTPError as error:
    if error.code != 401:
        raise SystemExit(1) from error
