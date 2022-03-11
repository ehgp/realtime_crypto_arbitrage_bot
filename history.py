"""Historical Market Data."""
from kucoin.client import Market
import sqlite3
import datetime as dt
import requests
import time
import json

url = "https://api.kucoin.com"
start_date = "2022-02-20 10:00:00.000"
end_date = "2022-02-20 10:01:00.000"
start_at = int(
    dt.datetime.timestamp(dt.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f"))
)
end_at = int(
    dt.datetime.timestamp(dt.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S.%f"))
)
symbol = "all"
kline_type = "1min"
res = requests.get(
    url
    + f"/api/v1/market/candles?type={kline_type}&symbol={symbol}&startAt={start_at}&endAt={end_at}"
)

# jsonRes = res.json()
with open("Output.txt", "w") as text_file:
    text_file.write(str(res.text))

# for i in range(len(jsonRes["data"].values())):
#     print(jsonRes["data"])
#     print(len(jsonRes["data"][i]["ticker"]))
# for x in range(len(jsonRes['data'][i]['ticker']):

# placeholders[9] = dt.datetime.fromtimestamp(jsonResponse["data"]["time"] / 1e3)

# for i in range(len(jsonResponse["data"])):
#     print(i)
# time	timestamp
# symbol	Symbol
# symbolName	Name of trading pairs, it would change after renaming
# buy	Best bid price
# sell	Best ask price
# changeRate	24h change rate
# changePrice	24h change price
# high	Highest price in 24h
# low	Lowest price in 24h
# vol	24h volume, executed based on base currency
# volValue	24h traded amount
# last	Last traded price
# averagePrice	Average trading price in the last 24 hours
# takerFeeRate	Basic Taker Fee
# makerFeeRate	Basic Maker Fee
# takerCoefficient	Taker Fee Coefficient
# makerCoefficient	Maker Fee Coefficient
