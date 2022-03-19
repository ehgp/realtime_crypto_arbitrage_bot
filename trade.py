"""Trade."""
import os
import yaml
import pandas as pd
from kucoin.client import Trade
import sqlite3
import logging
import logging.config
from pathlib import Path
import datetime as dt

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


def order_handling(order):
    """Check if order went through."""
    table = "trade_info"
    con = sqlite3.connect("db/kucoin.db")
    df = pd.read_sql_query(f"SELECT * FROM {table}", con)
    status_order = df[df["orderId"] == order["orderId"]]["type"]
    if status_order is None:
        order_handling(order)
    elif status_order == "filled":
        return True
    elif status_order == "cancelled":
        return False
    else:
        order_handling(order)


def execute_fwd_tri_arbitrage(client, row, cost):
    """Execute Forward Triangle Arbitrage."""
    size = cost / row["ca_bsta"]  # bc_bsta,ba_bstb
    if size < row["ca_bstasize"]:
        order_ca = client.create_limit_order(
            symbol=f"{row['c']}-{row['a']}",
            side="buy",
            price=str(row["ca_bsta"]),
            size=str(size),
            remark="test",
            stp="CN",
            trade_type="TRADE",
            time_in_force="FOK",
        )
    else:
        size = row["ca_bstasize"]
        order_ca = client.create_limit_order(
            symbol=f"{row['c']}-{row['a']}",
            side="buy",
            price=str(row["ca_bsta"]),
            size=str(size),
            remark="test",
            stp="CN",
            trade_type="TRADE",
            time_in_force="FOK",
        )
    if order_handling(order_ca) is True:
        size = (row["ca_bsta"] * size) / row["bc_bsta"]  # bc_bsta,ba_bstb
        if size < row["bc_bstasize"]:
            order_bc = client.create_limit_order(
                symbol=f"{row['b']}-{row['c']}",
                side="buy",
                price=str(row["bc_bsta"]),
                size=str(size),
                remark="test",
                stp="CN",
                trade_type="TRADE",
                time_in_force="FOK",
            )
        else:
            size = row["bc_bstasize"]
            order_bc = client.create_limit_order(
                symbol=f"{row['b']}-{row['c']}",
                side="buy",
                price=str(row["bc_bsta"]),
                size=str(size),
                remark="test",
                stp="CN",
                trade_type="TRADE",
                time_in_force="FOK",
            )
        if order_handling(order_bc) is True:
            size = (row["bc_bsta"] * size) / row["ba_bstb"]  # bc_bsta,ba_bstb
            if size < row["ba_bstbsize"]:
                order_bc = client.create_limit_order(
                    symbol=f"{row['b']}-{row['a']}",
                    side="sell",
                    price=str(row["ba_bstb"]),
                    size=size,
                    remark="test",
                    stp="CN",
                    trade_type="TRADE",
                    time_in_force="FOK",
                )
            else:
                size = row["ba_bstbsize"]
                order_bc = client.create_limit_order(
                    symbol=f"{row['b']}-{row['a']}",
                    side="sell",
                    price=str(row["ba_bstb"]),
                    size=size,
                    remark="test",
                    stp="CN",
                    trade_type="TRADE",
                    time_in_force="FOK",
                )
            if order_handling(order_bc) is True:
                logger.info("Forward Triangle Arbitrage successful")
                return True
            else:
                logger.info("Order 3 not filled successfully, cancelling arbitrage op")
                return False
        else:
            logger.info("Order 2 not filled successfully, cancelling arbitrage op")
            return False
    else:
        logger.info("Order 1 not filled successfully, cancelling arbitrage op")
        return False


def execute_rev_tri_arbitrage(client, row, cost):
    """Execute Reverse Triangle Arbitrage."""
    size = cost / row["ba_bsta"]  # bc_bstb,ca_bstb
    if size < row["ba_bstasize"]:
        order_ca = client.create_limit_order(
            symbol=f"{row['b']}-{row['a']}",
            side="buy",
            price=str(row["ba_bsta"]),
            size=str(size),
            remark="test",
            stp="CN",
            trade_type="TRADE",
            time_in_force="FOK",
        )
    else:
        size = row["ba_bstasize"]
        order_ca = client.create_limit_order(
            symbol=f"{row['b']}-{row['a']}",
            side="buy",
            price=str(row["ba_bsta"]),
            size=str(size),
            remark="test",
            stp="CN",
            trade_type="TRADE",
            time_in_force="FOK",
        )
    if order_handling(order_ca) is True:
        size = (row["ba_bsta"] * size) / row["bc_bstb"]  # bc_bstb,ca_bstb
        if size < row["bc_bstbsize"]:
            order_bc = client.create_limit_order(
                symbol=f"{row['b']}-{row['c']}",
                side="sell",
                price=str(row["bc_bstb"]),
                size=str(size),
                remark="test",
                stp="CN",
                trade_type="TRADE",
                time_in_force="FOK",
            )
        else:
            size = row["bc_bstbsize"]
            order_bc = client.create_limit_order(
                symbol=f"{row['b']}-{row['c']}",
                side="sell",
                price=str(row["bc_bstb"]),
                size=str(size),
                remark="test",
                stp="CN",
                trade_type="TRADE",
                time_in_force="FOK",
            )
        if order_handling(order_bc) is True:
            size = (row["bc_bstb"] * size) / row["ca_bstb"]  # bc_bstb,ca_bstb
            if size < row["ca_bstbsize"]:
                order_bc = client.create_limit_order(
                    symbol=f"{row['c']}-{row['a']}",
                    side="sell",
                    price=str(row["ca_bstb"]),
                    size=size,
                    remark="test",
                    stp="CN",
                    trade_type="TRADE",
                    time_in_force="FOK",
                )
            else:
                size = row["ca_bstbsize"]
                order_bc = client.create_limit_order(
                    symbol=f"{row['c']}-{row['a']}",
                    side="sell",
                    price=str(row["ca_bstb"]),
                    size=size,
                    remark="test",
                    stp="CN",
                    trade_type="TRADE",
                    time_in_force="FOK",
                )
            if order_handling(order_bc) is True:
                logger.info("Reverse Triangle Arbitrage successful")
                return True
            else:
                logger.info("Order 3 not filled successfully, cancelling arbitrage op")
                return False
        else:
            logger.info("Order 2 not filled successfully, cancelling arbitrage op")
            return False
    else:
        logger.info("Order 1 not filled successfully, cancelling arbitrage op")
        return False


def execute_triangular_arbitrage():
    """Execute Triangular Arbitrage."""
    cf = _load_config()
    cost = cf["fiat_cost_per_trade"]
    api_key = cf["KUCOIN_YOUR_API_KEY"]
    api_secret = cf["KUCOIN_YOUR_SECRET"]
    api_passphrase = cf["KUCOIN_YOUR_PASS"]
    client = Trade(
        key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=True
    )
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
            "ba_bstbsize": "float",
            "ba_bstasize": "float",
            "bc_bstb": "float",
            "bc_bsta": "float",
            "bc_bstbsize": "float",
            "bc_bstasize": "float",
            "ca_bstb": "float",
            "ca_bsta": "float",
            "ca_bstbsize": "float",
            "ca_bstasize": "float",
            "fwd_arb": "float",
            "rev_arb": "float",
            "attempted": "str",
        }
    )
    df = df[df["attempted"] == "N"]
    df.fillna(0, inplace=True)
    for i, row in df.iterrows():
        logger.info(
            "Execute triangular arbitrage for trio: %s,%s,%s"
            % (row["a"], row["b"], row["c"])
        )
        if row["fwd_arb"] > row["rev_arb"]:
            execute_fwd_tri_arbitrage(client, row, cost)
            update_table = "UPDATE %s SET %s = %s WHERE %s = %s;" % (
                table,
                "attempted",
                "Y",
                "fwd_arb",
                row["fwd_arb"],
            )
            logger.info("Updating a row of data")
            cur.execute(update_table)
            con.commit()
            con.close()
        elif row["rev_arb"] > row["fwd_arb"]:
            execute_rev_tri_arbitrage(client, row, cost)
            update_table = "UPDATE %s SET %s = %s WHERE %s = %s;" % (
                table,
                "attempted",
                "Y",
                "rev_arb",
                row["rev_arb"],
            )
            logger.info("Updating a row of data")
            cur.execute(update_table)
            con.commit()
            con.close()
        else:
            logger.info(
                "Opportunities yield same profit percentage, attempting fwd instead"
            )
            execute_fwd_tri_arbitrage(client, row, cost)


if __name__ == "__main__":
    execute_triangular_arbitrage()
