"""Do your Data Science here."""

import sqlite3
import pandas as pd
import numpy as np
import datetime as dt

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
    print("Creating Table arb_ops")
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
        print("Inserting a row of data")
        cur.execute(insert_table)
        con.commit()
    con.close()
    arb_op.to_csv("arbitrage_ops.csv", index=False)


def find_bellman_ford_ops():
    """Find Bellman Ford Opportunities."""
    return None


if __name__ == "__main__":
    find_tri_arb_ops()
