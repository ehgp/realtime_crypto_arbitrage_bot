"""Account Info."""
from socket import MSG_CMSG_CLOEXEC
import pandas as pd
import asyncio
from codecs import lookup
import sqlite3
import os
import yaml
from kucoin.client import WsToken
from kucoin.ws_client import KucoinWsClient
import datetime as dt
import re


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

# pandas controls on how much data to see
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)


async def main():
    """Execute Main."""

    async def deal_msg(msg):
        """Message Handler."""
        if msg["topic"] == "/account/balance":
            print(f'got {msg["subject"]}:{msg["data"]}')
            con = sqlite3.connect("db/kucoin.db")
            cur = con.cursor()
            table = "acc_bal"
            placeholders = list(msg["data"].values()).append(
                dt.datetime.fromtimestamp(msg["time"] / 1e3)
            )
            placeholders = ",".join('"' + str(e) + '"' for e in placeholders)
            columns = ", ".join(msg["data"].keys())
            create_table = """CREATE TABLE IF NOT EXISTS acc_bal \
        (total text, available text,  availableChange text, \
        currency text, hold text, holdChange text, relationEvent text, relationEventId text, \
        relationContext text, time text, )"""
            print("Creating Table acc_info")
            cur.execute(create_table)
            con.commit()
            insert_table = "INSERT INTO %s ( %s ) VALUES ( %s )" % (
                table,
                columns,
                placeholders,
            )
            print(insert_table)
            print("Inserting a row of data")
            cur.execute(insert_table)
            con.commit()
            con.close()
        if msg["topic"] == "/spotMarket/tradeOrders":
            print(f'got {msg["subject"]}:{msg["data"]}')
            con = sqlite3.connect("db/kucoin.db")
            cur = con.cursor()
            table = "trade_info"
            placeholders = list(msg["data"].values())
            placeholders[12] = dt.datetime.fromtimestamp(placeholders[12] / 1e3)
            placeholders = ",".join('"' + str(e) + '"' for e in placeholders)
            columns = ", ".join(msg["data"].keys())
            create_table = """CREATE TABLE IF NOT EXISTS trade_info \
        (symbol text, orderType text,  side text, \
        orderId text, type text, orderTime text, size text, filledSize text, \
        price text, clientOid text, remainSize text, status text, ts text, )"""
            print("Creating Table trade_info")
            cur.execute(create_table)
            con.commit()
            insert_table = "INSERT INTO %s ( %s ) VALUES ( %s )" % (
                table,
                columns,
                placeholders,
            )
            print(insert_table)
            print("Inserting a row of data")
            cur.execute(insert_table)
            con.commit()
            con.close()

    # is public
    # client = WsToken()
    # is private
    # client = WsToken(key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=False, url='')
    # is sandbox
    client = WsToken(
        key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=True
    )
    ws_client = await KucoinWsClient.create(loop, client, deal_msg, private=False)
    # await ws_client.subscribe("/market/ticker:ETH-USDT")
    # await ws_client.subscribe("/market/ticker:all")
    await ws_client.subscribe("/account/balance")
    await ws_client.subscribe("/spotMarket/tradeOrders")
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
