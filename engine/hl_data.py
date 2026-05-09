"""
Hyperliquid public market data fetcher.
Fetches 1h OHLCV candles for the active universe.
"""
from __future__ import annotations
import json
import time
import urllib.request
import urllib.error
from typing import Optional
import pandas as pd

from .config import HL_REST


def _post(payload: dict, retries: int = 3, timeout: int = 15) -> Optional[list]:
    body = json.dumps(payload).encode()
    for i in range(retries):
        try:
            req = urllib.request.Request(
                HL_REST, data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
            if i == retries - 1:
                print(f"[hl_data] POST failed after {retries}: {e}", flush=True)
                return None
            time.sleep(min(10, 2 ** i))
    return None


def fetch_candles(coin: str, interval: str = "1h", n_bars: int = 200) -> Optional[pd.DataFrame]:
    """
    Fetch last `n_bars` 1h candles for `coin` from HL.
    Returns DataFrame with [open, high, low, close, volume] indexed by timestamp.
    """
    end_ms = int(time.time() * 1000)
    bar_ms = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}.get(interval, 3_600_000)
    start_ms = end_ms - n_bars * bar_ms

    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
        },
    }
    data = _post(payload)
    if not data:
        return None
    if not isinstance(data, list) or len(data) == 0:
        return None

    rows = []
    for c in data:
        try:
            rows.append({
                "ts": int(c["t"]),
                "open": float(c["o"]),
                "high": float(c["h"]),
                "low": float(c["l"]),
                "close": float(c["c"]),
                "volume": float(c["v"]),
            })
        except (KeyError, ValueError, TypeError):
            continue
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("ts").sort_index()
    return df


def fetch_meta() -> Optional[dict]:
    """Get HL universe metadata (sz_decimals, max_leverage, etc.)."""
    return _post({"type": "meta"})


def fetch_mids() -> Optional[dict]:
    """Get current mid prices for all coins."""
    return _post({"type": "allMids"})
