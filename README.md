# fib-continuation-v1

Paper-trading service for the fib-retracement continuation engine.
Validated by cyber-psycho mining (2026-05-09): OOS PF 1.27, MDD -18%, n=204.
Unifies dead-cat + autofib + find-trade fib-leg under one mechanic.

Mechanic: detect ≥3% impulse over ≤20 bars. When price retraces to fib 0.618
without breaking 0.886 invalidation, fire CONTINUATION trade in impulse direction.
SL = invalidate ± 1×ATR, TP = 1× extension, hold 96h.

Universe: 8 perp-coins (BTC, ETH, SOL, LINK, AVAX, DOGE, BNB, XRP).

## Endpoints
- GET /health — liveness
- GET /state — engine state + open positions + active impulse candidates
- GET /trades — last N closed trades
- GET /closures — for backtest-match-tracker
- POST /halt / POST /resume — operator control

## Mode
Default: PAPER. The detector tracks impulse candidates in memory across scans.
Restart loses pending candidates; that's acceptable for paper.
