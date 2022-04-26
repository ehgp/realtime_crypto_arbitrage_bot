# UMBC Data 606 Capstone: Real Time Arbitrage Bot

Kucoin supported websockets implementation of real time arbitrage opportunity bot.

Relies on four scripts:

* live:<br>
Websockets real time feed of price data.

* trade:<br>
Trading module for execution of arbitrage trades.

* analysis:<br>
actual implementation of ML models.

1. Reverse and Forward Triangular Arbitrage in analysis.py
2. Bellman Ford Optimization in bellmanford.py

* account:<br>
Websockets real time account and trade implementation.

Features:<br>
Github CICD Pipeline<br>
SQLite implementation<br>
Docker containerization with docker compose<br>
Github Pages Sphinx Documentation

## Documentation

Documentation found [here](https://ehgp.github.io/data_606_capstone/)

## Requirements

* Python 3.7
* Docker Desktop >= 4.5.1
* Pipenv 2022.1.8

## Installation

Fill out parameters.yaml

```yaml
KUCOIN_YOUR_API_KEY: ${KUCOIN_YOUR_API_KEY}
KUCOIN_YOUR_SECRET: ${KUCOIN_YOUR_SECRET}
KUCOIN_YOUR_PASS: ${KUCOIN_YOUR_PASS}
# trade.py parameters
fiat_cost_per_trade: 50.00
fiat_unit_per_trade: USD
# historical.py and forecasting.py parameters
url: "https://api.kucoin.com"
start_date: "2022-03-10 10:00:00"
end_date: "2022-03-10 10:05:00"
kline_type: "1min"
# bellman ford parameters
exchange: 'Kucoin'
# taker fee in decimal
taker_fee: 0.001
# tri arb parameters
minimum_perc_tri_arb_profit: 0.1
```

To use docker you must have docker desktop available with docker compose:

You can use either pipenv or your base python installation (default is requirements):<br>
Pipenv:<br>
pipenv install<br>
pipenv run python live.py

Requirements:<br>
pip install -r requirements.txt<br>
python live.py

## Authors

Erick Garcia<br>
Daniel Abbasi<br>
Yuksel Baris Dokuzoglu

## Disclosure

Use are your own risk and do your own research.<br>
Not responsible for lost funds.

## Support

We started this project as a capstone project with no profit taking.<br>
To continue this project development, support is heavily recommended and appreciated.<br>
We accept donations in cryptocurrencies, anything helps. Thank you.

BTC: 3G3zsvcxgomdERYTSjeX4iBJYMfFfCgFmn

ETH: 0x227cc9c06db03563300fa7c2d0b0a34b370f5987

DOGE: DNNsSrk767w9K1eaqc2tQSvJ4mzfBpw4RP

BNB: bnb1rlka4xf6h8p8nlpf8szczmcyugdktptstgham0

XMR: 86vsoW6jsTzcvGZxKVG1PxfsSqUzrMuqvKxLGCXZ3RcNY7VyvhcgiimciW5ZsHyrKUGCpqFPjDG7iMu9sSoveZDxMeGpqCb

ZCASH: t1fkojdhoTTQmrPSExCLMuV6D3a2jxESGtL

ADA: DdzFFzCqrhtBuwQRtRKNSVca58HDwicLx5aDWn8K5pyg36665BL5s6WBLAc9bCTxWk15MFiefoerCRiuxysW7Sy4RQJ6UM2vWXoCg98z

## TODO

[Gemini](https://docs.gemini.com/rest-api/#sandbox) and [Coinbase](https://docs.cloud.coinbase.com/exchange/docs/sandbox) sandbox implementations.