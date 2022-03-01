#  MarketData
from kucoin.client import Market
import sqlite3
import datetime as dt
import requests
import time

url = "https://api.kucoin.com"
start_date = "2022-02-20"
end_date = "2022-02-21"
symbol = "BTC-USDT"
kline_type = "1min"
start_at = int(dt.datetime.timestamp(dt.datetime.strptime(start_date, "%Y-%m-%d")))
end_at = int(dt.datetime.timestamp(dt.datetime.strptime(end_date, "%Y-%m-%d")))
res = requests.get(
    url
    + f"/api/v1/market/candles?type={kline_type}&symbol={symbol}&startAt={start_at}&endAt={end_at}"
)
for i in range(len(res["data"])):