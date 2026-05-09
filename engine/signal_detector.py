"""
Fib Retracement CONTINUATION signal detector.

Validated by cyber-psycho mining (2026-05-09):
  HF: IS PF=1.32  eq=$21,581  MDD=-30%
      OOS PF=1.27  eq=$13,314  MDD=-18%   n_oos=204
  56 walk-forward survivor cells in parameter grid.

Mechanic: detect ≥3% impulse over ≤20 bars. Set virtual LIMIT at fib 0.618
retrace. If price tags target without breaking 0.886 invalidation, fire
CONTINUATION signal in the impulse direction.

This detector is stateful: it tracks active impulse candidates per coin in
memory. On each evaluate_latest_bar call it (a) checks if any active
candidate filled or invalidated this bar, then (b) detects new impulses.

SL = invalidate ± 1×ATR, TP = 1× extension, max hold 96 bars.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Optional

from .config import FIB_PARAMS, TRADE_PARAMS

# In-memory candidate state per coin: {coin: [{end_idx, side, tgt, inv, ext, ts}, ...]}
# Invariant: candidates expire after FIB_PARAMS["max_wait_bars"] bars.
_CANDIDATES = {}


def calc_atr(highs, lows, closes, period=14):
    h_s = pd.Series(highs)
    l_s = pd.Series(lows)
    pc = pd.Series(closes).shift(1)
    tr = pd.concat([h_s - l_s, (h_s - pc).abs(), (l_s - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean().values


def detect_latest_impulse(closes, highs, lows, min_pct, lookback, min_bars):
    """Look at the latest bar — does it complete an impulse from any of the last
    `lookback` bars? Returns dict if so, else None.
    """
    n = len(closes)
    i = n - 1
    for jb in range(min_bars, min(lookback + 1, i + 1)):
        j = i - jb
        if lows[j] > 0:
            up = (closes[i] - lows[j]) / lows[j]
            if up >= min_pct:
                return {
                    "start_idx": j, "end_idx": i, "side": "UP",
                    "start_px": float(lows[j]), "end_px": float(closes[i]),
                }
        if highs[j] > 0:
            dn = (highs[j] - closes[i]) / highs[j]
            if dn >= min_pct:
                return {
                    "start_idx": j, "end_idx": i, "side": "DN",
                    "start_px": float(highs[j]), "end_px": float(closes[i]),
                }
    return None


def evaluate_for_coin(df: pd.DataFrame, coin: str) -> Optional[dict]:
    """Coin-aware evaluator. Maintains _CANDIDATES[coin] across calls."""
    if len(df) < FIB_PARAMS["candles_history"]:
        return None

    closes = df["close"].values.astype(float)
    highs = df["high"].values.astype(float)
    lows = df["low"].values.astype(float)
    atr = calc_atr(highs, lows, closes, FIB_PARAMS["atr_period"])

    i = len(df) - 1
    if np.isnan(atr[i]) or atr[i] <= 0:
        return None

    # Initialize state list
    if coin not in _CANDIDATES:
        _CANDIDATES[coin] = []

    # Step 1: check existing candidates against this bar
    surviving = []
    fired_signal = None
    cur_high = float(highs[i])
    cur_low = float(lows[i])

    for c in _CANDIDATES[coin]:
        # expire if too old
        if i - c["end_idx"] > FIB_PARAMS["max_wait_bars"]:
            continue
        # check invalidation FIRST
        if c["side"] == "UP":
            if cur_low <= c["inv"]:
                continue  # invalidated
            if cur_low <= c["tgt"]:
                fired_signal = c
                continue
        else:  # DN
            if cur_high >= c["inv"]:
                continue
            if cur_high >= c["tgt"]:
                fired_signal = c
                continue
        surviving.append(c)
    _CANDIDATES[coin] = surviving

    # Step 2: detect new impulse on this bar (only if no signal fired and not in cooldown)
    if fired_signal is None:
        new_imp = detect_latest_impulse(
            closes, highs, lows,
            FIB_PARAMS["min_imp_pct"],
            FIB_PARAMS["impulse_lookback"],
            FIB_PARAMS["min_impulse_bars"],
        )
        if new_imp is not None:
            lo = min(new_imp["start_px"], new_imp["end_px"])
            hi = max(new_imp["start_px"], new_imp["end_px"])
            rng = hi - lo
            if rng > 0:
                if new_imp["side"] == "UP":
                    tgt = hi - FIB_PARAMS["fib_target"] * rng
                    inv = hi - FIB_PARAMS["fib_invalidate"] * rng
                    ext = hi + FIB_PARAMS["tp_extension"] * rng
                else:
                    tgt = lo + FIB_PARAMS["fib_target"] * rng
                    inv = lo + FIB_PARAMS["fib_invalidate"] * rng
                    ext = lo - FIB_PARAMS["tp_extension"] * rng
                _CANDIDATES[coin].append({
                    "start_idx": new_imp["start_idx"],
                    "end_idx": i,
                    "side": new_imp["side"],
                    "tgt": float(tgt),
                    "inv": float(inv),
                    "ext": float(ext),
                })

    if fired_signal is None:
        return None

    # Build trade signal from fired candidate
    side = fired_signal["side"]  # impulse direction
    if side == "UP":
        raw_direction = "long"
        is_long = True
        sl_buf = fired_signal["inv"] - FIB_PARAMS["sl_buffer_atr"] * float(atr[i])
        if sl_buf >= fired_signal["tgt"]:
            return None
        tp_px_f = fired_signal["ext"]
        if tp_px_f <= fired_signal["tgt"]:
            return None
    else:
        raw_direction = "short"
        is_long = False
        sl_buf = fired_signal["inv"] + FIB_PARAMS["sl_buffer_atr"] * float(atr[i])
        if sl_buf <= fired_signal["tgt"]:
            return None
        tp_px_f = fired_signal["ext"]
        if tp_px_f >= fired_signal["tgt"]:
            return None

    fade_direction = raw_direction  # CONTINUATION — no inversion

    return {
        "fire_ts": df.index[i],
        "ref_price": float(fired_signal["tgt"]),  # we treat the fib target as the entry ref
        "atr": float(atr[i]),
        "raw_direction": raw_direction,
        "fade_direction": fade_direction,
        "trade_side": "B" if is_long else "A",
        "is_long": is_long,
        "sl_px": float(sl_buf),
        "tp_px": float(tp_px_f),
        "max_hold_bars": TRADE_PARAMS["max_hold_bars"],
        "fib_target_pct": float(FIB_PARAMS["fib_target"]),
        "impulse_side": side,
        "impulse_start_idx": int(fired_signal["start_idx"]),
        "impulse_end_idx": int(fired_signal["end_idx"]),
        "bw_percentile": 0.0,
        "vol_spike": 0.0,
        "momentum": 0.0,
        "bb_upper": 0.0,
        "bb_lower": 0.0,
        "bb_mid": 0.0,
    }


def evaluate_latest_bar(df: pd.DataFrame) -> Optional[dict]:
    """
    Stateless wrapper for the case where caller doesn't pass a coin.
    The fib engine NEEDS state across calls — server.py must call evaluate_for_coin.

    This wrapper exists for trader/persistence compat. Returns None (signals
    only fire via evaluate_for_coin which gets the coin context).
    """
    return None
