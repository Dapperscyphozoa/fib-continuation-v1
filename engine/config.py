"""
fib-continuation-v1 engine config.
LOCKED parameters (HF variant) from validated walk-forward
(cyber-psycho mining 2026-05-09):
  IS  PF=1.32  eq=$21,581  MDD=-30%
  OOS PF=1.27  eq=$13,314  MDD=-18%   n_oos=204
"""
import os

ENGINE_NAME = "fib-continuation-v1"
CLOID_PREFIX = "fibhf_"
ENGINE_VERSION = "1.0.0"

LIVE_TRADING = os.environ.get("LIVE_TRADING", "0") == "1"
PAPER_MODE = not LIVE_TRADING
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
USE_TESTNET = os.environ.get("USE_TESTNET", "0") == "1"

LIVE_MIN_ACCOUNT_VALUE = float(os.environ.get("LIVE_MIN_ACCOUNT_VALUE", "200"))
LIVE_SIZE_SCALE = float(os.environ.get("LIVE_SIZE_SCALE", "0.25"))
LIVE_EXIT_SLIPPAGE = float(os.environ.get("LIVE_EXIT_SLIPPAGE", "0.05"))
LIVE_MAKER_ONLY_ENTRIES = os.environ.get("LIVE_MAKER_ONLY_ENTRIES", "1") == "1"

HL_REST = "https://api.hyperliquid.xyz/info"
HL_EXCHANGE = "https://api.hyperliquid.xyz/exchange"
HL_WALLET = os.environ.get("HL_WALLET", "0x3eDaD0649Db466E6E7B9a0Caa3E5d6ddc71B5ffE")
HL_PRIVATE_KEY = os.environ.get("HL_PRIVATE_KEY", "")

PM_URL = os.environ.get("PM_URL", "https://portfolio-manager-7df2.onrender.com")
PM_CHECK_ENABLED = os.environ.get("PM_CHECK_ENABLED", "0") == "1"

# Same 8-coin universe as cvd-inverted-v1 / vol-mom-inverted-v1.
# Mining coverage: BTC, ETH, SOL, LINK, AVAX, DOGE, BNB, XRP.
PRIMARY_UNIVERSE = ["SOL", "LINK", "AVAX", "ETH"]
SECONDARY_UNIVERSE = ["BTC", "DOGE", "BNB", "XRP"]
BLOCKED_UNIVERSE = []
ACTIVE_UNIVERSE = PRIMARY_UNIVERSE + SECONDARY_UNIVERSE

FIB_PARAMS = {
    "timeframe": "1h",
    "min_imp_pct": 0.03,            # ≥3% impulse
    "impulse_lookback": 20,         # over ≤20 bars
    "min_impulse_bars": 4,
    "fib_target": 0.618,            # entry on retrace to 0.618
    "fib_invalidate": 0.886,        # SL anchor on break of 0.886
    "tp_extension": 1.0,            # 1× extension beyond impulse extreme
    "sl_buffer_atr": 1.0,           # SL = inv ± 1×ATR
    "max_wait_bars": 20,            # candidate expires after 20 bars
    "atr_period": 14,
    "candles_history": 200,
}

TRADE_PARAMS = {
    "direction_method": "fib_retrace_continuation",
    "sl_atr_mult": 1.0,             # already encoded in fib geometry; kept for display
    "tp_atr_mult": 1.0,
    "max_hold_bars": 96,            # 4 days
    "fee_bps_taker": 4.5,
    "fee_bps_maker": 1.0,
    "min_signal_gap_bars": 12,
}

# Alias for trader / persistence compat
SQUEEZE_PARAMS = FIB_PARAMS

RISK_PCT_PER_TRADE = float(os.environ.get("RISK_PCT_PER_TRADE", "0.01"))
LEVERAGE = int(os.environ.get("LEVERAGE", "5"))
MAX_NOTIONAL_PER_TRADE = float(os.environ.get("MAX_NOTIONAL_PER_TRADE", "100"))

# Fixed-notional override. When > 0, position_size() ignores risk-based
# computation entirely and returns exactly this dollar notional per trade.
# Set via Render env. Default 0 = disabled (use risk-based sizing).
FIXED_NOTIONAL_USD = float(os.environ.get("FIXED_NOTIONAL_USD", "0"))

MAX_OPEN_POSITIONS = int(os.environ.get("MAX_OPEN_POSITIONS", "4"))

SCAN_INTERVAL_SEC = int(os.environ.get("SCAN_INTERVAL_SEC", "300"))
POSITION_CHECK_INTERVAL_SEC = int(os.environ.get("POSITION_CHECK_INTERVAL_SEC", "60"))

STATE_DIR = os.environ.get("STATE_DIR", "/var/data")
DB_FILE = os.environ.get("DB_FILE", "fibcont.db")

HTTP_PORT = int(os.environ.get("PORT", "10000"))

HALT_STATE = {"active": False, "reason": None, "ts": None}
