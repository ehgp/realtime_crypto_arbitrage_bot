"""Analysis.

This script executes the models that find arbitrage opportunities.
Currently two arbitrage models are being used:
1.Triangular Arbitrage.
2.Bellman Ford Optimization.
"""

import datetime as dt
import logging
import logging.config
import os
import sqlite3
from pathlib import Path

import pandas as pd
import yaml

from bellmanford import (bellman_ford_exec,  # draw_graph_to_png,
                         load_exchange_graph,
                         print_profit_opportunity_for_path_store_db)
from triarb import find_tri_arb_ops

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


def triangular_arbitrage():
    """Execute Triangular Arbitrage."""
    logger.info("Finding Triangle Arbitrage Opportunities")
    find_tri_arb_ops()


def bellman_ford_arbitrage():
    """Execute Bellman Ford Arbitrage."""
    logger.info("Finding Opportunities Using Bellman Ford")
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
        print_profit_opportunity_for_path_store_db(
            graph, path, depth=True, starting_amount=starting_amount
        )


if __name__ == "__main__":
    triangular_arbitrage()
    bellman_ford_arbitrage()
