"""Trade."""
from kucoin import client
import pandas as pd

# pandas controls on how much data to see
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)

df = pd.read_csv("arbitrage_ops.csv")
for i, row in df.iterrows():

    cost = 50.00
    size = str(cost / df["ba_bstb"])

    order_ba = client.create_limit_order(
        symbol=f"{df['b']}-{df['a']}",
        side="buy",
        price=str(df["ba_bstb"]),
        size=size,
        remark="test",
        stp="CN",
        trade_type="TRADE",
        time_in_force="FOK",
    )


# stop=,stop_price=,cancel_after=,)

# :param symbol: Name of symbol e.g. KCS-BTC
# :type symbol: string
# :param side: buy or sell
# :type side: string
# :param price: Name of coin
# :type price: string
# :param size: Amount of base currency to buy or sell
# :type size: string
# :param client_oid: (optional) Unique order_id  default flat_uuid()
# :type client_oid: string
# :param remark: (optional) remark for the order, max 100 utf8 characters
# :type remark: string
# :param stp: (optional) self trade protection CN, CO, CB or DC (default is None)
# :type stp: string
# :param trade_type: (optional) The type of trading : TRADE（Spot Trade）, MARGIN_TRADE (Margin Trade). Default is TRADE
# :type trade_type: string
# :param time_in_force: (optional) GTC, GTT, IOC, or FOK (default is GTC)
# :type time_in_force: string
# :param stop: (optional) stop type loss or entry - requires stop_price
# :type stop: string
# :param stop_price: (optional) trigger price for stop order
# :type stop_price: string
# :param cancel_after: (optional) number of seconds to cancel the order if not filled
#     required time_in_force to be GTT
# :type cancel_after: string
# :param post_only: (optional) indicates that the order should only make liquidity. If any part of
#     the order results in taking liquidity, the order will be rejected and no part of it will execute.
# :type post_only: bool
# :param hidden: (optional) Orders not displayed in order book
# :type hidden: bool
# :param iceberg:  (optional) Only visible portion of the order is displayed in the order book
# :type iceberg: bool
# :param visible_size: (optional) The maximum visible size of an iceberg order
# :type visible_size: bool
