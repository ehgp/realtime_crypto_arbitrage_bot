"""Historical Market Data all tickers for forecasting.

For all tickers available in Kucoin API, get historical data for all of them according to the following parameters:
start_date, end_date, kline_type
"""
import pandas as pd
import sqlite3
import datetime as dt
import requests
import os
import yaml
import logging
import logging.config
from pathlib import Path


def _load_config():
    """Load the configuration yaml and return dictionary of setttings.

    Returns:
        yaml as a dictionary.
    """
    config_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(config_path, "../parameters.yaml")
    with open(config_path, "r") as config_file:
        config_defs = yaml.safe_load(config_file.read())

    if config_defs.values() is None:
        raise ValueError("parameters yaml file incomplete")

    return config_defs


# Logging
path = Path(os.getcwd())
Path("log").mkdir(parents=True, exist_ok=True)
log_config = Path(path, "log_config.yaml")
timestamp = "{:%Y_%m_%d_%H_%M_%S}".format(dt.datetime.now())
with open(log_config, "r") as log_file:
    config_dict = yaml.safe_load(log_file.read())
    # Append date stamp to the file name
    log_filename = config_dict["handlers"]["file"]["filename"]
    base, extension = os.path.splitext(log_filename)
    base2 = "_" + os.path.splitext(os.path.basename(__file__))[0] + "_"
    log_filename = "{}{}{}{}".format(base, base2, timestamp, extension)
    config_dict["handlers"]["file"]["filename"] = log_filename
    logging.config.dictConfig(config_dict)
logger = logging.getLogger(__name__)

cf = _load_config()

url = cf["url"]
start_date = cf["start_date"]
end_date = cf["end_date"]
kline_type = cf["kline_type"]


symbols = []
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
con = sqlite3.connect("../db/kucoin.db")
historical_df.to_sql(name="historical_all_tickers", con=con, index=False)
df = pd.read_sql_query("select * from historical_all_tickers", con=con)
con.close()
print(df.head(5))
print("Number of rows and columns:", df.shape)
