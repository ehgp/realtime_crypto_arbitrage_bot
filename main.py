import asyncio

from kucoin.client import Client
from kucoin.asyncio import KucoinSocketManager
from getpass import getpass
from getpass import getuser
import keyring
import os
import yaml

# Leverages Windows Credential Manager and Mac Keychain to store credentials
# and also makes environment variables that store your credentials in your computer
# dsns = [
#     "KUCOIN_YOUR_API_KEY",
#     "KUCOIN_YOUR_SECRET",
#     "KUCOIN_YOUR_PASS",
# ]

# user = getuser()
# for dsn in dsns:
#     if keyring.get_password(dsn, user) is None:
#         prompt = f"Please input {dsn}: "
#         password = getpass(prompt=prompt, stream=None)
#         keyring.set_password(dsn, user, password)

# logger.info("Get Credentials")
# user = getuser()
# fb_email = keyring.get_password("FACEBOOK_EMAIL", user)
# fb_pass = keyring.get_password("FACEBOOK_PASSWORD", user)
# if (fb_email or fb_pass) is None:
#     logger.info("Incomplete credentials")
#     exit()

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

api_key = cf['KUCOIN_YOUR_API_KEY']
api_secret = cf['KUCOIN_YOUR_SECRET']
api_passphrase = cf['KUCOIN_YOUR_PASS']


async def main():
    global loop

    # callback function that receives messages from the socket
    async def handle_evt(msg):
        if msg["topic"] == "/market/ticker:ETH-USDT":
            print(f'got ETH-USDT tick:{msg["data"]}')

        elif msg["topic"] == "/market/snapshot:BTC":
            print(f'got BTC market snapshot:{msg["data"]}')

        elif msg["topic"] == "/market/snapshot:KCS-BTC":
            print(f'got KCS-BTC symbol snapshot:{msg["data"]}')

        elif msg["topic"] == "/market/ticker:all":
            print(f'got all market snapshot:{msg["data"]}')

        elif msg["topic"] == "/account/balance":
            print(f'got account balance:{msg["data"]}')

        elif msg["topic"] == "/market/level2:KCS-BTC":
            print(f'got L2 msg:{msg["data"]}')

        elif msg["topic"] == "/market/match:BTC-USDT":
            print(f'got market match msg:{msg["data"]}')

        elif msg["topic"] == "/market/level3:BTC-USDT":
            if msg["subject"] == "trade.l3received":
                if msg["data"]["type"] == "activated":
                    # must be logged into see these messages
                    print(f"L3 your order activated: {msg['data']}")
                else:
                    print(f"L3 order received:{msg['data']}")
            elif msg["subject"] == "trade.l3open":
                print(f"L3 order open: {msg['data']}")
            elif msg["subject"] == "trade.l3done":
                print(f"L3 order done: {msg['data']}")
            elif msg["subject"] == "trade.l3match":
                print(f"L3 order matched: {msg['data']}")
            elif msg["subject"] == "trade.l3change":
                print(f"L3 order changed: {msg['data']}")

    client = Client(api_key, api_secret, api_passphrase)

    ksm = await KucoinSocketManager.create(loop, client, handle_evt)

    # for private topics such as '/account/balance' pass private=True
    ksm_private = await KucoinSocketManager.create(
        loop, client, handle_evt, private=True
    )

    # Note: try these one at a time, if all are on you will see a lot of output

    # ETH-USDT Market Ticker
    await ksm.subscribe("/market/ticker:ETH-USDT")
    # BTC Symbol Snapshots
    await ksm.subscribe("/market/snapshot:BTC")
    # KCS-BTC Market Snapshots
    await ksm.subscribe("/market/snapshot:KCS-BTC")
    # All tickers
    await ksm.subscribe("/market/ticker:all")
    # Level 2 Market Data
    await ksm.subscribe("/market/level2:KCS-BTC")
    # Market Execution Data
    await ksm.subscribe("/market/match:BTC-USDT")
    # Level 3 market data
    await ksm.subscribe("/market/level3:BTC-USDT")
    # Account balance - must be authenticated
    await ksm_private.subscribe("/account/balance")

    while True:
        print("sleeping to keep loop open")
        await asyncio.sleep(20, loop=loop)


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
