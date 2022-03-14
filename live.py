"""Real Time Crypto Bot."""
import asyncio
from kucoin.client import WsToken
from kucoin.ws_client import KucoinWsClient
from codecs import lookup
import sqlite3
import os
import yaml
import datetime as dt
import re
from analysis import find_tri_arb_ops
from trade import execute_triangular_arbitrage

"""Please note that the system will frozen the
fees from the orders that entered the order book in advance. Read List Fills
to learn more. Well that sucks."""


def _load_config():
    """Load the configuration yaml and return dictionary of setttings.

    Returns:
        yaml as a dictionary.
    """
    config_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(config_path, "creds.yaml")
    with open(config_path, "r") as config_file:
        config_defs = yaml.safe_load(config_file.read())

    if config_defs.values() is None:
        raise ValueError("creds yaml file incomplete")

    return config_defs


cf = _load_config()

api_key = cf["KUCOIN_YOUR_API_KEY"]
api_secret = cf["KUCOIN_YOUR_SECRET"]
api_passphrase = cf["KUCOIN_YOUR_PASS"]


async def main():
    """Execute Main."""

    async def deal_msg(msg):
        """Message Handler."""
        if msg["topic"] == "/market/ticker:all":
            print(f'got {msg["subject"]} tick:{msg["data"]}')
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
            print("Creating Table tickers")
            cur.execute(create_table)
            con.commit()
            insert_table = "INSERT INTO %s ( %s, %s, %s ) VALUES ( %s )" % (
                table,
                "quoteTick",
                "baseTick",
                columns,
                placeholders,
            )
            print("Inserting a row of data")
            cur.execute(insert_table)
            con.commit()
            con.close()
            find_tri_arb_ops()
            # execute_triangular_arbitrage()

    # is public
    client = WsToken()
    # is private
    # client = WsToken(key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=False, url='')
    # is sandbox
    # client = WsToken(
    #     key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=True
    # )
    ws_client = await KucoinWsClient.create(loop, client, deal_msg, private=False)
    # await ws_client.subscribe("/market/ticker:ETH-USDT")
    await ws_client.subscribe("/market/ticker:all")
    # await ws_client.subscribe("/account/balance")
    # await ws_client.subscribe("/spotMarket/tradeOrders")
    while True:
        print("sleeping to keep loop open")
        await asyncio.sleep(60, loop=loop)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt as e:
        print(f"Closing Loop {e}")
        pass
