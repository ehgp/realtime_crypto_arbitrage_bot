# UMBC Data 606 Capstone: Real Time Arbitrage Bot

Kucoin supported websockets implementation of real time arbitrage opportunity bot.

Relies on four scripts:

live:
Websockets real time feed of price data.

trade:
Trading module for execution of arbitrage trades.

analysis:
actual implementation of ML models.

1. Reverse and Forward Triangular Arbitrage in analysis.py
2. Bellman Ford Optimization in bellmanford.py

account:
Websockets real time account and trade implementation.

Features:
Github CICD Pipeline
SQLite implementation
Docker containerization with docker compose
Github Pages Sphinx Documentation

## Documentation

Documentation found [here](https://ehgp.github.io/data_606_capstone/)

## Requirements

* Python 3.7
* Docker Desktop >= 4.5.1
* Pipenv 2021.11.23

## Installation

Fill out credentials in parameters.yaml

To use docker you must have docker desktop available with docker compose:

You can use either pipenv or your base python installation (default is requirements):
Pipenv:
pipenv install
pipenv run pytnon main.py

Requirements:
pip install -r requirements.txt
python main.py

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

Add trading implementation of bellman ford profit in bf_arb_ops table.
