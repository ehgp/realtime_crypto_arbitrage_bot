import asyncio
import sqlite3
import os
import yaml
from kucoin.client import WsToken
from kucoin.ws_client import KucoinWsClient

# def _load_config():
#     """Load the configuration yaml and return dictionary of setttings.

#     Returns:
#         yaml as a dictionary.
#     """
#     config_path = os.path.dirname(os.path.realpath(__file__))
#     config_path = os.path.join(config_path, "creds.yaml")
#     with open(config_path, "r") as config_file:
#         config_defs = yaml.safe_load(config_file.read())

#     if config_defs.values() is None:
#         raise ValueError("creds yaml file incomplete")

#     return config_defs


# cf = _load_config()

# api_key = cf["KUCOIN_YOUR_API_KEY"]
# api_secret = cf["KUCOIN_YOUR_SECRET"]
# api_passphrase = cf["KUCOIN_YOUR_PASS"]


async def main():
    async def deal_msg(msg):
        if msg["topic"] == "/market/ticker:ETH-USDT":
            print(f'got ETH-USDT tick:{msg["data"]}')
            con = sqlite3.connect("kucoin.db")
            cur = con.cursor()
            table = "tickers"
            placeholders = list(msg["data"].values())
            placeholders.insert(0, "ETH-USDT")
            placeholders = ",".join('"' + str(e) + '"' for e in placeholders)
            columns = ", ".join(msg["data"].keys())
            create_table = """CREATE TABLE IF NOT EXISTS tickers
                         (ticker text,  bestAsk text, bestAskSize text, bestBid text, bestBidSize text, price text, sequence text, size text, time text
                         )"""
            print("Creating Table")
            cur.execute(create_table)
            con.commit()
            insert_table = "INSERT INTO %s ( %s, %s ) VALUES ( %s )" % (
                table,
                "ticker",
                columns,
                placeholders,
            )
            print("Inserting a row of data")
            cur.execute(insert_table)
            con.commit()
            con.close()

    # is public
    client = WsToken()
    # is private
    # client = WsToken(key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=False, url='')
    # is sandbox
    # client = WsToken(is_sandbox=True)
    ws_client = await KucoinWsClient.create(loop, client, deal_msg, private=False)
    await ws_client.subscribe("/market/ticker:ETH-USDT")
    while True:
        print("sleeping to keep loop open")
        await asyncio.sleep(60, loop=loop)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
