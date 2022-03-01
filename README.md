# Data 606 Capstone: Real Time Arbitrage Bot

This software currently relies on four elements.

kucoin-feed:
Websockets real time feed of price data.

sqlite:
SQLite DB that will store this real time data for processing and training.

history:
Gather historical data from HTTPS for training

analysis:
actual implementation of ML model.

## Requirements

* Python 3.7
* Docker Desktop >= 4.5.1

## Installation

Fill out credentials in creds.yaml

To use docker you must have docker desktop available with docker compose:

You can use pipenv or your base python installation:
Pipenv:
pipenv install
pipenv run pytnon main.py

Requirements:
pip install -r requirements.txt
python main.py

## Authors

Erick Garcia
Daniel Abbasi
Yuksel Baris Dokuzoglu