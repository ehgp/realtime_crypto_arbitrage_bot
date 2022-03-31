# Data 606 Capstone: Real Time Arbitrage Bot

Kucoin supported websockets implementation of real time arbitrage opportunity bot.

Relies on four scripts:

live:
Websockets real time feed of price data.

trade:
Trading module for execution of arbitrage trades.

analysis:
actual implementation of ML model.

account:
Websockets real time account and trade implementation.

## Documentation

Documentation found [here](https://ehgp.github.io/data_606_capstone/)

## Requirements

* Python 3.7
* Docker Desktop >= 4.5.1
* Pipenv 2021.11.23

## Installation

Fill out credentials in parameters.yaml

To use docker you must have docker desktop available with docker compose:

You can use pipenv or your base python installation:
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
