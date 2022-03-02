"""Do your Data Science here please."""

import sqlite3
import pandas as pd

cnx = sqlite3.connect("db/kucoin.db")

df = pd.read_sql_query("SELECT * FROM tickers", cnx)

print(df["quoteTick"].unique())
print(df["baseTick"].unique())

df_fil = df[(df["quoteTick"] == "DOGE") | (df["baseTick"] == "DOGE")]
print(df_fil)
# USDT/bestBid-fee to DOGE, DOGE/bestAsk-fee to BTC, BTC/bestAsk-fee to USDT
