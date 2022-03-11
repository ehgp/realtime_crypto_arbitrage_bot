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


def execute_triangle_arbitrage():
    """Execute Triangle Arbitrage."""
    cnx = sqlite3.connect("db/kucoin.db")

    df = pd.read_sql_query("SELECT * FROM tickers", cnx)
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

    arb_op.rename(columns={"baseTick": "c", "quoteTick": "a"}, inplace=True)

    arb_op.dropna(inplace=True)

    arb_op["fwd_arb"] = (
        (arb_op["ba_bstb"] * 1.001)
        * (1 / (arb_op["bc_bsta"] * 1.001))
        * (1 / (arb_op["ca_bsta"] * 1.001))
        - 1
    ) * 100
    arb_op["rev_arb"] = (
        arb_op["bc_bstb"]
        * 1.001
        * arb_op["ca_bstb"]
        * 1.001
        * (1 / (arb_op["ba_bsta"] * 1.001))
        - 1
    ) * 100

    arb_op.loc[~(arb_op["fwd_arb"] > 0), "fwd_arb"] = np.nan
    arb_op.loc[~(arb_op["rev_arb"] > 0), "rev_arb"] = np.nan
    arb_op_fwd = (
        arb_op.sort_values("fwd_arb", ascending=False)
        .groupby("fwd_arb")
        .head(2)
        .reset_index(drop=True)
    )
    arb_op_rev = (
        arb_op.sort_values("rev_arb", ascending=False)
        .groupby("rev_arb")
        .head(2)
        .reset_index(drop=True)
    )
    arb_op = arb_op_fwd.append(arb_op_rev)
    arb_op.dropna(subset=["fwd_arb", "rev_arb"], how="all", inplace=True)
    arb_op.drop_duplicates(inplace=True)
    arb_op.to_csv("arbitrage_ops.csv", index=False)
