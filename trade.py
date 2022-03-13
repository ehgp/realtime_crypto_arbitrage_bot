"""Trade."""
import pandas as pd
from kucoin import client
import sqlite3


def execute_fwd_tri_arbitrage():
    """Execute Forward Triangle Arbitrage."""
    size = str(cost / row["ba_bstb"])  # bc_bsta,ca_bsta
    # order_ba = client.create_limit_order(
    #     symbol=f"{row['b']}-{row['a']}",
    #     side="buy",
    #     price=str(row["ba_bstb"]),
    #     size=size,
    #     remark="test",
    #     stp="CN",
    #     trade_type="TRADE",
    #     time_in_force="FOK",
    # )
    return None


def execute_rev_tri_arbitrage():
    """Execute Reverse Triangle Arbitrage."""
    size = str(cost / row["bc_bstb"])  # ca_bstb,ba_bsta
    return None


cost = 50.00
table = "arb_ops"
con = sqlite3.connect("db/kucoin.db")
cur = con.cursor()
df = pd.read_sql_query(f"SELECT * FROM {table}", con)
df = df.astype(
    {
        "a": "str",
        "b": "str",
        "c": "str",
        "ba_bstb": "float",
        "ba_bsta": "float",
        "bc_bstb": "float",
        "bc_bsta": "float",
        "ca_bstb": "float",
        "ca_bsta": "float",
        "fwd_arb": "float",
        "rev_arb": "float",
        "attempted": "str",
    }
)
df = df[df["attempted"] == "N"]

for i, row in df.iterrows():
    if row["fwd_arb"] > row["rev_arb"]:
        execute_fwd_tri_arbitrage()
        update_table = "UPDATE %s SET %s = %s WHERE %s = %s;" % (
            table,
            "attempted",
            "Y",
            "fwd_arb",
            row["fwd_arb"],
        )
        print("Updating a row of data")
        cur.execute(update_table)
        con.commit()
        con.close()
    elif row["rev_arb"] > row["fwd_arb"]:
        execute_rev_tri_arbitrage()
        update_table = "UPDATE %s SET %s = %s WHERE %s = %s;" % (
            table,
            "attempted",
            "Y",
            "rev_arb",
            row["rev_arb"],
        )
        print("Updating a row of data")
        cur.execute(update_table)
        con.commit()
        con.close()
    else:
        print("Opportunities yield same profit percentage, attempting fwd instead")
        execute_fwd_tri_arbitrage()

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
