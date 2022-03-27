"""Historical Market Data all tickers for forecasting.

For all tickers available in Kucoin API, get historical data for all of them according to the following parameters:
start_date, end_date, kline_type
"""
import pandas as pd
import datetime as dt
import requests
import sqlite3

symbols = []
url = "https://api.kucoin.com"
res = requests.get(url + "/api/v1/market/allTickers")

jsonRes = res.json()
for i in jsonRes["data"]["ticker"]:
    symbols.append(i["symbol"])
print("Number of symbols: ", len(symbols))

# pandas controls on how much data to see
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)
historical_df = pd.DataFrame()
df_list = []
url = "https://api.kucoin.com"
start_date = "2021-02-20 00:00:00"
end_date = "2022-02-20 00:00:00"
kline_type = "1day"
start_at = int(
    dt.datetime.timestamp(dt.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S"))
)
end_at = int(dt.datetime.timestamp(dt.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")))
for i in range(len(symbols)):
    symbol = symbols[i]
    res = requests.get(
        url
        + "/api/v1/market/candles?type=%s&symbol=%s&startAt=%s&endAt=%s"
        % (kline_type, symbol, start_at, end_at)
    )

    jsonRes = res.json()
    if "data" in jsonRes.keys():
        for j in jsonRes["data"]:
            j[0] = dt.datetime.fromtimestamp(int(j[0]))
            df_list.append([symbol] + j)
    else:
        pass
historical_df = historical_df.append(
    pd.DataFrame(
        df_list,
        columns=[
            "symbol",
            "start_time",
            "opening_price",
            "closing_price",
            "highest_price",
            "lowest_price",
            "transaction_amount",
            "transaction_volume",
        ],
    )
)
con = sqlite3.connect("db/kucoin.db")
historical_df.to_sql(name="historical_all_tickers", con=con, index=False)
df = pd.read_sql_query("select * from historical_all_tickers", con=con)
con.close()
print(df.head(5))
print("Number of rows and columns:", df.shape)
