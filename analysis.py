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
from bellmanford import (
    bellman_ford_exec,
    print_profit_opportunity_for_path,
    load_exchange_graph,
    draw_graph_to_png,
)

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


def _load_config():
    """Load the configuration yaml and return dictionary of setttings.

    Returns:
        yaml as a dictionary.
    """
    config_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(config_path, "parameters.yaml")
    with open(config_path, "r") as config_file:
        config_defs = yaml.safe_load(config_file.read())

    if config_defs.values() is None:
        raise ValueError("parameters yaml file incomplete")

    return config_defs


cf = _load_config()


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
    table = "tri_arb_ops"
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
            '"%s"' % (dt.datetime.now()),
        )
        logger.info("Inserting a row of data")
        cur.execute(insert_table)
        con.commit()
    con.close()
    arb_op.to_csv("arbitrage_ops.csv", index=False)


def bellman_ford_graph():
    """Execute Bellman Ford Graph."""
    con = sqlite3.connect("db/kucoin.db")
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
    graph = load_exchange_graph(
        exchange=cf["exchange"], dataframe=df, fees=True, depth=True, log=True
    )
    # to execute this drawing you will need to replace line 188
    # import pydotplus as pydot in C:\ProgramData\Miniconda3\Lib\site-packages\networkx\drawing\nx_pydot.py
    # and install graphviz executable if you are in windows.
    # draw_graph_to_png(graph, to_file="graph.png")
    paths = bellman_ford_exec(graph, unique_paths=True, depth=True)
    for path, starting_amount in paths:
        # Note that depth=True and starting_amount are set in this example
        print_profit_opportunity_for_path(
            graph, path, depth=True, starting_amount=starting_amount
        )


if __name__ == "__main__":
    # find_tri_arb_ops()
    bellman_ford_graph()
