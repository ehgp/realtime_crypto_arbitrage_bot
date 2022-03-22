"""Could you do your Data Science Analysis here please."""

import sqlite3
import pandas as pd
import numpy as np
import datetime as dt
import logging
import logging.config
from pathlib import Path
import yaml
import os

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


# pandas controls on how much data to see
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)


def find_tri_arb_ops():
    """Find Triangle Arbitrage Opportunities."""
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
    df.to_csv("market.csv", index=False)

    combo = [
        [a, b, c]
        for a in df["quoteTick"].unique()
        for b in df["baseTick"].unique()
        for c in df["quoteTick"].unique()
    ]
    arb_op = pd.DataFrame(combo, columns=["a", "b", "c"], dtype=str)

    arb_op.reset_index(drop=True, inplace=True)

    arb_op.rename(columns={"b": "baseTick", "a": "quoteTick"}, inplace=True)

    arb_op["ba_bstb"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestBid"]

    arb_op["ba_bsta"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestAsk"]

    arb_op["ba_bstbsize"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestBidSize"]

    arb_op["ba_bstasize"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestAskSize"]

    arb_op.rename(columns={"baseTick": "b", "quoteTick": "a"}, inplace=True)
    arb_op.rename(columns={"b": "baseTick", "c": "quoteTick"}, inplace=True)

    arb_op["bc_bstb"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestBid"]

    arb_op["bc_bsta"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestAsk"]

    arb_op["bc_bstbsize"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestBidSize"]

    arb_op["bc_bstasize"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestAskSize"]

    arb_op.rename(columns={"baseTick": "b", "quoteTick": "c"}, inplace=True)
    arb_op.rename(columns={"c": "baseTick", "a": "quoteTick"}, inplace=True)

    arb_op["ca_bstb"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestBid"]

    arb_op["ca_bsta"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestAsk"]

    arb_op["ca_bstbsize"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestBidSize"]

    arb_op["ca_bstasize"] = arb_op.merge(
        df,
        on=["baseTick", "quoteTick"],
        how="left",
    )["bestAskSize"]

    arb_op.rename(columns={"baseTick": "c", "quoteTick": "a"}, inplace=True)

    arb_op.dropna(inplace=True)

    """
    ::: NOTES :::
    =============
    EX: left_x_right
    Want left = 1/Ask
    Want right = Bid
    FORWARD ARBITRAGE (EX: ETHBTC) -> a = USDT, b = ETH, c = BTC
    ========================================================================
    # 1. buy BTCUSDT   - ask  <- pay for lowest asking price (faster)
    # 2. buy ETHBTC    - ask  <- pay for lowest asking price (faster)
    # 3. sell ETHUSDT  - bid  <- sell to top bid price (faster)
    REVERSE ARBITRAGE (EX: ETHBTC) -> a = USDT, b = ETH, c = BTC
    ========================================================================
    # 1. buy ETHUSDT   - ask  <- pay for lowest asking price (faster)
    # 2. sell ETHBTC   - bid  <- sell to top bid price (faster)
    # 3. sell BTCUSDT  - bid  <- sell to top bid price (faster)
    """

    arb_op["fwd_arb"] = (
        (1 / (arb_op["ca_bsta"] * 1.001))
        * (1 / (arb_op["bc_bsta"] * 1.001))
        * (arb_op["ba_bstb"] * 1.001)
        - 1
    ) * 100
    arb_op["rev_arb"] = (
        (1 / (arb_op["ba_bsta"] * 1.001))
        * (arb_op["bc_bstb"] * 1.001)
        * (arb_op["ca_bstb"] * 1.001)
        - 1
    ) * 100

    # Traditional arbitrage
    # arb_op["fwd_arb"] = (
    #     (arb_op["ba_bstb"] * 1.001)
    #     * (1 / (arb_op["bc_bsta"] * 1.001))
    #     * (1 / (arb_op["ca_bsta"] * 1.001))
    #     - 1
    # ) * 100
    # arb_op["rev_arb"] = (
    #     arb_op["bc_bstb"]
    #     * 1.001
    #     * arb_op["ca_bstb"]
    #     * 1.001
    #     * (1 / (arb_op["ba_bsta"] * 1.001))
    #     - 1
    # ) * 100

    arb_op.loc[~(arb_op["fwd_arb"] > 0.1), "fwd_arb"] = np.nan
    arb_op.loc[~(arb_op["rev_arb"] > 0.1), "rev_arb"] = np.nan
    arb_op = arb_op.loc[arb_op[["fwd_arb", "rev_arb"]].idxmax()]
    arb_op.dropna(subset=["fwd_arb", "rev_arb"], how="all", inplace=True)
    arb_op.drop_duplicates(inplace=True)
    table = "arb_ops"
    create_table = """CREATE TABLE IF NOT EXISTS arb_ops \
(a text, b text,  c text, ba_bstb text, ba_bsta text, ba_bstbsize text, ba_bstasize text, bc_bstb text, \
bc_bsta text, bc_bstbsize text, bc_bstasize text, ca_bstb text, ca_bsta text, ca_bstbsize text, ca_bstasize text, \
fwd_arb text, rev_arb text, attempted text, time text, \
UNIQUE (fwd_arb, rev_arb) ON CONFLICT IGNORE)"""
    logger.info("Creating Table arb_ops")
    cur.execute(create_table)
    con.commit()
    for i, row in arb_op.iterrows():
        placeholders = ",".join('"' + str(e) + '"' for e in row)
        columns = ", ".join(arb_op.columns)
        insert_table = "INSERT INTO %s ( %s, %s, %s ) VALUES ( %s, %s, %s )" % (
            table,
            columns,
            "attempted",
            "time",
            placeholders,
            '"N"',
            f'"{dt.datetime.now()}"',
        )
        logger.info("Inserting a row of data")
        cur.execute(insert_table)
        con.commit()
    con.close()
    arb_op.to_csv("arbitrage_ops.csv", index=False)


class TestSingleExchange(TestCase):
    def test_load_exchange_graph(self):
        currencies = ["BTC", "ETH", "USD", "LTC"]
        tickers = {
            "BTC/USD": {"bid": 5995, "ask": 6000, "bidVolume": 0.5, "askVolume": 0.9},
            "ETH/BTC": {"bid": 0.069, "ask": 0.07, "bidVolume": 0.5, "askVolume": 21},
            "ETH/USD": {"bid": 495, "ask": 500, "bidVolume": 30, "askVolume": 0.9},
            "LTC/USD": {"bid": 81, "ask": 82, "bidVolume": 0.5, "askVolume": 0.9},
            "LTC/BTC": {"bid": 0.121, "ask": 0.122, "bidVolume": 0.5, "askVolume": 0.9},
            "LTC/ETH": {"bid": 90, "ask": 100, "bidVolume": 0.5, "askVolume": 0.9},
        }
        symbols = [symbol for symbol in tickers.keys()]
        markets = {symbol: {"taker": 0.001} for symbol in symbols}
        exchange = TestExchange(
            name="a",
            currencies=currencies,
            tickers=tickers,
            symbols=symbols,
            markets=markets,
        )

        graph = asyncio.get_event_loop().run_until_complete(
            load_exchange_graph(
                exchange,
                name=False,
                fees=True,
                suppress=[""],
                depth=True,
                tickers=tickers,
            )
        )

        for symbol, quote_data in tickers.items():
            base, quote = symbol.split("/")
            self.assertEqual(
                graph[base][quote]["weight"],
                -math.log(quote_data["bid"] * (1 - markets[symbol]["taker"])),
            )
            self.assertEqual(
                graph[base][quote]["depth"], -math.log(quote_data["bidVolume"])
            )

            self.assertEqual(
                graph[quote][base]["weight"],
                -math.log((1 - markets[symbol]["taker"]) / quote_data["ask"]),
            )
            self.assertEqual(
                graph[quote][base]["depth"],
                -math.log(quote_data["askVolume"] * quote_data["ask"]),
            )

            self.assertEqual(symbol, graph[base][quote]["market_name"])


if __name__ == "__main__":
    find_tri_arb_ops()
