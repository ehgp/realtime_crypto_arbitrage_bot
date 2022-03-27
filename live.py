"""Real Time Crypto Bot.

This is the main execution of Real Time Websocket Client to gather ticker bid/ask price and size.
Those tickers will be stored as rows in a SQLite database for analysis.py to output profitable trading opportunities
for trade.py to execute.

Currently two arbitrage models are being used:
1.Triangular Arbitrage.
2.Bellman Ford Optimization.
"""
import asyncio
from kucoin.client import WsToken
from kucoin.ws_client import KucoinWsClient
import sqlite3
import os
import yaml
import datetime as dt
import logging
import logging.config
from pathlib import Path
from analysis import find_tri_arb_ops, bellman_ford_graph
from trade import execute_triangular_arbitrage


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

api_key = cf["KUCOIN_YOUR_API_KEY"]
api_secret = cf["KUCOIN_YOUR_SECRET"]
api_passphrase = cf["KUCOIN_YOUR_PASS"]


async def main():
    """Execute Main."""

    async def deal_msg(msg: dict) -> None:
        """Message Handler.

        Args:
            msg: dictionary containing subject and data of request.

        Returns:
            database storage and function actions.
        """
        if msg["topic"] == "/market/ticker:all":
            logger.info("got %s tick: %s" % (msg["subject"], msg["data"]))
            con = sqlite3.connect("db/kucoin.db")
            cur = con.cursor()
            table = "tickers"
            placeholders = list(msg["data"].values())
            placeholders.insert(0, msg["subject"].replace("-", " ").split(" ")[0])
            placeholders.insert(0, msg["subject"].replace("-", " ").split(" ")[1])
            placeholders[9] = dt.datetime.fromtimestamp(placeholders[9] / 1e3)
            placeholders = ",".join('"' + str(e) + '"' for e in placeholders)
            columns = ", ".join(msg["data"].keys())
            create_table = """CREATE TABLE IF NOT EXISTS tickers \
(baseTick text, quoteTick text,  bestAsk text, \
bestAskSize text, bestBid text, bestBidSize text, price text, sequence text, \
size text, time text
                         )"""
            logger.info("Creating Table tickers")
            cur.execute(create_table)
            con.commit()
            insert_table = "INSERT INTO %s ( %s, %s, %s ) VALUES ( %s )" % (
                table,
                "quoteTick",
                "baseTick",
                columns,
                placeholders,
            )
            logger.info("Inserting a row of data")
            cur.execute(insert_table)
            con.commit()
            con.close()
            # find_tri_arb_ops()
            bellman_ford_graph()
            # execute_triangular_arbitrage()

    # is public
    client = WsToken()
    # is private
    # client = WsToken(key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=False)
    # is sandbox
    # client = WsToken(
    #     key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=True
    # )
    ws_client = await KucoinWsClient.create(loop, client, deal_msg, private=False)
    await ws_client.subscribe("/market/ticker:all")
    while True:
        logger.info("sleeping to keep loop open")
        await asyncio.sleep(60, loop=loop)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt as e:
        logger.info("Closing Loop %r", e)
        pass
