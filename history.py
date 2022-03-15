"""Historical Market Data."""
from kucoin.client import Market
import pandas as pd
import sqlite3
import datetime as dt
import requests
import time
import json

# pandas controls on how much data to see
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

con = sqlite3.connect("db/kucoin.db")
cur = con.cursor()
df = pd.read_sql_query("SELECT * FROM tickers", con)
df = df.astype(
    {
        "baseTick": "str",
        "quoteTick": "str",
        "bestAsk": "float",
        "bestAskSize": "float",
        "bestBid": "float",
        "bestBidSize": "float",
        "price": "float",
        "sequence": "float",
        "size": "float",
        "time": "str",
    }
)
df["time"] = pd.to_datetime(df["time"], infer_datetime_format=True)
df = df.sort_values("time").drop_duplicates(["baseTick", "quoteTick"], keep="last")
df.reset_index(drop=True, inplace=True)
df.sort_values("baseTick", inplace=True)
df.reset_index(drop=True, inplace=True)

url = "https://api.kucoin.com"
start_date = "2022-03-10 10:00:00"
end_date = "2022-03-10 10:05:00"
kline_type = "1min"

start_at = int(
    dt.datetime.timestamp(dt.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S"))
)
end_at = int(dt.datetime.timestamp(dt.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")))
for i, row in df.iterrows():
    symbol = f"{row['baseTick']}-{row['quoteTick']}"

    res = requests.get(
        url
        + f"/api/v1/market/candles?type={kline_type}&symbol={symbol}&startAt={start_at}&endAt={end_at}"
    )

    jsonRes = res.json()
    try:
        for i in jsonRes["data"]:
            con = sqlite3.connect("db/kucoin.db")
            cur = con.cursor()
            table = "historical"
            placeholders = i
            placeholders.insert(0, row["quoteTick"])
            placeholders.insert(0, row["baseTick"])
            placeholders[2] = dt.datetime.fromtimestamp(int(placeholders[2]))
            placeholders = ",".join('"' + str(e) + '"' for e in placeholders)
            columns = ", ".join(
                [
                    "quoteTick",
                    "baseTick",
                    "start_time",
                    "opening_price",
                    "closing_price",
                    "highest_price",
                    "lowest_price",
                    "transaction_amount",
                    "transaction_volume",
                ]
            )
            create_table = """CREATE TABLE IF NOT EXISTS historical (quoteTick text, baseTick text, start_time text, opening_price text, closing_price text, highest_price text, lowest_price text, transaction_amount text, transaction_volume text)"""
            print("Creating Table historical")
            cur.execute(create_table)
            con.commit()
            insert_table = "INSERT INTO %s ( %s ) VALUES ( %s )" % (
                table,
                columns,
                placeholders,
            )
            print("Inserting a row of data")
            cur.execute(insert_table)
            con.commit()
            con.close()
    except Exception as e:
        print(f"Exception Error {e}")
        pass
