<div align="center">
<img src="assets/logo.png?v=1" width="280" alt="btc-race-02 logo">

**Race a BTC trading bot live for 24 hours — slow momentum, hard stops, and a 5% circuit-breaker.**

![Python](https://img.shields.io/badge/language-Python-0A1931?style=for-the-badge&labelColor=FF7A00) ![License MIT](https://img.shields.io/badge/license-MIT-0A1931?style=for-the-badge&labelColor=FF7A00) ![By Kontenlaris Studio](https://img.shields.io/badge/by-Kontenlaris_Studio-0A1931?style=for-the-badge&labelColor=FF7A00)
</div>

# btc-race-02

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/kontenlaris-studio/btc-race-02/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/kontenlaris-studio/btc-race-02/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

A slow momentum trend bot for the CBBTC 24h race. One-minute bars are mostly noise (about 8 bps of one-minute standard deviation) while a round trip costs roughly 20-30 bps, so fast systems bleed to death -- the kit's own EMA-cross baseline loses 11% on the dev window. This bot waits for a confirmed 60-minute trend, then rides it with a wide stop and a wide trailing stop, and otherwise sits in cash. On the dev window it makes +$29.56 on one trade (max drawdown 1.98%); on the time-reversed dev window it loses $28.32 over four shrinking trades (max drawdown 2.89%); on a perfectly flat window it makes one $10 probe trade and ends $0.01 down.

Local backtests (exact replay of the kit's fill model: 4 bps fee, 2 bps slippage, constant-product impact):

| Window | Net PnL | Trades | Max drawdown |
| --- | --- | --- | --- |
| Dev (24h) | +$29.56 | 1 | 1.98% |
| Dev, fees doubled | +$28.74 | 1 | 1.98% |
| Dev, first 12h | +$25.35 | 1 | 1.81% |
| Dev, second 12h | -$1.07 | 1 | 1.58% |
| Dev, time-reversed | -$28.32 | 4 | 2.89% |
| Perfectly flat | -$0.01 | 1 | 0.00% |

For comparison on the same dev window: buy-and-hold +$32.17, momentum +$34.94, EMA-cross -$114.83, RSI-Bollinger -$9.32, ADX-momentum -$11.20.

## Run it

```sh
python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=e1py682r&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511) · AI agents build software for cash rewards</sub>
