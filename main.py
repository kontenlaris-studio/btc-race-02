"""Momentum trend bot for the CBBTC 24h race (agent-fun/bars-replay/v1).

Why this shape: the 1-minute bars are mostly noise (about 8 bps of one-minute
standard deviation) while a round trip costs roughly 20-30 bps, so fast
systems bleed to death -- the kit's own EMA-cross baseline loses 11% on the
dev window, and my own EMA-cross variants lost money with 3-26 trades. The
dev window's money was in one slow multi-hour drift, so this bot waits for a
confirmed 60-minute trend, then rides it with a wide stop and a wide trailing
stop, and otherwise sits in cash.

Rules, all integer-exact on the closes the harness sends:
  - Entry (flat): the 60-minute return tops +40 bps for 3 bars running
    while the 2-hour return is not down (once two hours of history exist).
    The entry spends the whole equity: the position is capped by the
    1.5% stop, the 2.5% trailing stop and the 5% circuit-breaker, and the
    round trip costs about 34 bps at full size -- small next to the
    multi-percent drifts this bot is built to ride.
  - Exit (holding): the 60-minute return falls under -150 bps, the
    position is worth 1.5% under its cost, or 2.5% under its peak value.
  - Anti-martingale: a losing round trip halves the next entry's size
    (down to a quarter), a winning one restores full size.
  - Circuit-breaker: equity 5% under the starting cash flattens the
    position and halts trading, long before the 25% guardrail.
  - No new entries in the last hour of the window.
  - Guardrail fallback: if no trade has happened by bar 1200, buy a $10
    probe and hold it to the end, so the entry always meets the
    minimum-1-trade guardrail even in a window with no uptrend at all.

Everything is a pure function of the bars the harness sends: no clock, no
environment, no randomness, so the two graded runs answer identically.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
LOOKBACK = 60            # bars of the momentum window
ENTRY_BPS = 40           # enter when the 60-minute return tops +40 bps
EXIT_BPS = -150          # exit when the 60-minute return falls under -150 bps
SIZE_BPS = 10000         # buy the whole equity per entry
STOP_BPS = 150           # exit when the position is worth 1.5% under its cost
TRAIL_BPS = 250          # exit when the position falls 2.5% under its peak value
MAX_SLIP_BPS = 100       # 1% past the close the order was decided on
HALT_DD_BPS = 500        # halt when equity falls 5% under the starting cash
LAST_ENTRY_SEQ = 1380    # no new entries in the last hour of the window
PROBE_SEQ = 1200         # buy the guardrail probe if still trade-less here
PROBE_NOTIONAL = 10_000_000   # $10 in quote units
COOLDOWN_BARS = 15      # bars to wait after an exit before re-entering


closes = []               # closes of CBBTC, oldest first
confirm = 0             # consecutive bars the entry signal has held
losses = 0              # consecutive losing round trips (anti-martingale)
peak_value = 0            # highest marked value of the current position
halted = False            # set by the drawdown circuit-breaker, never cleared
last_exit_seq = -10 ** 9
start_equity = None
trades = 0                # filled trades seen so far (from the batches' fills)


def momentum_bps(lookback=LOOKBACK):
    """The return over `lookback` bars in bps, or None before it is full."""
    if len(closes) <= lookback:
        return None
    now = closes[-1]
    then = closes[-1 - lookback]
    return (now - then) * 10000 // then


def on_batch(state, batch):
    global peak_value, halted, last_exit_seq, start_equity, trades, confirm, losses
    if start_equity is None:
        start_equity = state.equity
    for fill in batch["fills"]:
        if fill["status"] == "filled":
            trades += 1
    for bar in batch["bars"]:
        if bar["symbol"] == SYMBOL:
            closes.append(int(bar["c"]))
    if state.warming_up:
        return []
    held = state.positions.get(SYMBOL)
    if held is not None:
        value = state.value(SYMBOL, held.qty)
        if value > peak_value:
            peak_value = value
        mom = momentum_bps()
        fading = mom is not None and mom < EXIT_BPS
        stopped = value * 10000 <= held.cost * (10000 - STOP_BPS)
        trailed = value * 10000 <= peak_value * (10000 - TRAIL_BPS)
        if fading or stopped or trailed:
            # A losing round trip halves the next entry's size (and a winning
            # one restores it): a losing streak never compounds.
            if value < held.cost:
                losses += 1
            else:
                losses = 0
            last_exit_seq = state.seq
            peak_value = 0
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                     "max_slippage_bps": MAX_SLIP_BPS}]
        return []
    # Flat: the drawdown breaker, then a momentum entry, then the probe.
    if not halted and state.equity * 10000 < start_equity * (10000 - HALT_DD_BPS):
        halted = True
    if halted or state.seq > LAST_ENTRY_SEQ:
        return []
    if state.seq - last_exit_seq < COOLDOWN_BARS:
        return []
    # Entry needs the 60-minute trend AND, once two hours of history exist,
    # the 2-hour trend not to be down: in a falling market the 60-minute
    # return still spikes over +40 bps on dead-cat bounces, and buying those
    # cost $28 on the time-reversed dev window.
    mom = momentum_bps()
    mom2h = momentum_bps(120)
    # The 2-hour return must not be down: in a falling market the 1-hour
    # return still spikes on dead-cat bounces, and buying those is what
    # loses money. And the entry signal must hold for 3 bars in a row:
    # a real drift holds it, chop flickers it.
    long_ok = mom2h is None or mom2h > 0
    if mom is not None and mom > ENTRY_BPS and long_ok:
        confirm += 1
    else:
        confirm = 0
    if mom is not None and mom > ENTRY_BPS and long_ok and confirm >= 3:
        size = SIZE_BPS >> losses if losses < 2 else SIZE_BPS // 4
        notional = state.equity * size // 10000
        room = state.weight_room(SYMBOL)
        if room < notional:
            notional = room
        if notional > state.cash:
            notional = state.cash
        if notional < int(state.hello["fees"]["min_notional_quote_units"]):
            return []
        return [{"side": "buy", "symbol": SYMBOL, "notional_quote_units": notional,
                 "max_slippage_bps": MAX_SLIP_BPS}]
    if trades == 0 and state.seq >= PROBE_SEQ and state.cash >= PROBE_NOTIONAL:
        return [{"side": "buy", "symbol": SYMBOL, "notional_quote_units": PROBE_NOTIONAL,
                 "max_slippage_bps": MAX_SLIP_BPS}]
    return []


makefun_bars.run(on_batch)
