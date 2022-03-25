"""Single Exchange Graph."""
import math
import networkx as nx
import datetime
import logging.config
import logging
from pathlib import Path
import yaml
import os
import datetime as dt

# Logging
path = Path(os.getcwd())
Path("log").mkdir(parents=True, exist_ok=True)
log_config = Path(os.path.abspath(path), "log_config.yaml")
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
    config_path = os.path.join(os.path.abspath(path), "parameters.yaml")
    with open(config_path, "r") as config_file:
        config_defs = yaml.safe_load(config_file.read())

    if config_defs.values() is None:
        raise ValueError("parameters yaml file incomplete")

    return config_defs


cf = _load_config()

__all__ = ["load_exchange_graph"]


def _add_weighted_edge_to_graph(
    graph: nx.DiGraph,
    base: str,
    quote: str,
    bid: float,
    ask: float,
    bidsize: float,
    asksize: float,
    time_tick: datetime,
    log=False,
    fees=False,
    depth=False,
):
    """todo: add global variable to bid_volume/ ask_volume to see if all tickers (for a given exchange) have value == None.

    Returns a Networkx DiGraph populated with the current ask and bid prices for each market in graph (represented by
    edges).
    :param exchange: A ccxt Exchange object
    :param market_name: A string representing a cryptocurrency market formatted like so:
    '{base_currency}/{quote_currency}'
    :param graph: A Networkx DiGraph upon
    :param log: If the edge weights given to the graph should be the negative logarithm of the ask and bid prices. This
    is necessary to calculate arbitrage opportunities.
    :param fees: If fees should be taken into account for prices.
    :param suppress: A list or set which tells which types of warnings to not throw. Accepted elements are 'markets'.
    :param ticker: A dictionary representing a market as returned by ccxt's Exchange's fetch_ticker method
    :param depth: If True, also adds an attribute 'depth' to each edge which represents the current volume of orders
    available at the price represented by the 'weight' attribute of each edge.
    """
    logger.info("Adding edge to graph")

    if fees:
        fee = cf["fee"]
    else:
        fee = 0

    fee_scalar = 1 - fee

    bid_rate = bid
    ask_rate = ask
    if depth:
        bid_volume = bidsize
        ask_volume = asksize

    base_currency = base
    quote_currency = quote
    market_name = "%s/%s" % (base, quote)

    if log:
        if depth:
            graph.add_edge(
                base_currency,
                quote_currency,
                weight=-math.log(fee_scalar * bid_rate),
                depth=-math.log(bid_volume),
                market_name=market_name,
                trade_type="SELL",
                fee=fee,
                volume=bid_volume,
                time_tick=time_tick,
                no_fee_rate=bid_rate,
            )
            graph.add_edge(
                quote_currency,
                base_currency,
                weight=-math.log(fee_scalar * 1 / ask_rate),
                depth=-math.log(ask_volume * ask_rate),
                market_name=market_name,
                trade_type="BUY",
                fee=fee,
                volume=ask_volume,
                time_tick=time_tick,
                no_fee_rate=ask_rate,
            )
        else:
            graph.add_edge(
                base_currency,
                quote_currency,
                weight=-math.log(fee_scalar * bid_rate),
                market_name=market_name,
                trade_type="SELL",
                fee=fee,
                time_tick=time_tick,
                no_fee_rate=bid_rate,
            )
            graph.add_edge(
                quote_currency,
                base_currency,
                weight=-math.log(fee_scalar * 1 / ask_rate),
                market_name=market_name,
                trade_type="BUY",
                fee=fee,
                time_tick=time_tick,
                no_fee_rate=ask_rate,
            )
    else:
        if depth:
            graph.add_edge(
                base_currency,
                quote_currency,
                weight=fee_scalar * bid_rate,
                depth=bid_volume,
                market_name=market_name,
                trade_type="SELL",
                fee=fee,
                volume=bid_volume,
                time_tick=time_tick,
                no_fee_rate=bid_rate,
            )
            graph.add_edge(
                quote_currency,
                base_currency,
                weight=fee_scalar * 1 / ask_rate,
                depth=ask_volume,
                market_name=market_name,
                trade_type="BUY",
                fee=fee,
                volume=ask_volume,
                time_tick=time_tick,
                no_fee_rate=ask_rate,
            )
        else:
            graph.add_edge(
                base_currency,
                quote_currency,
                weight=fee_scalar * bid_rate,
                market_name=market_name,
                trade_type="SELL",
                fee=fee,
                time_tick=time_tick,
                no_fee_rate=bid_rate,
            )
            graph.add_edge(
                quote_currency,
                base_currency,
                weight=fee_scalar * 1 / ask_rate,
                market_name=market_name,
                trade_type="BUY",
                fee=fee,
                time_tick=time_tick,
                no_fee_rate=ask_rate,
            )

    logger.info("Added edge to graph", market=market_name)


def load_exchange_graph(
    exchange, dataframe=None, fees=False, depth=False, log=False
) -> nx.DiGraph:
    """Return a networkx DiGraph populated with the current ask and bid prices for each market in graph.

    (represented by edges). If depth, also adds an attribute 'depth' to each edge which represents the current volume of orders
    available at the price represented by the 'weight' attribute of each edge.
    """
    logger.info("Initializing empty graph with exchange_name attribute")
    graph = nx.DiGraph()

    graph.graph["exchange_name"] = exchange

    logger.info("Initialized empty graph with exchange_name attribute")

    for idx, row in dataframe.iterrows():
        _add_weighted_edge_to_graph(
            graph=graph,
            base=row["baseTick"],
            quote=row["quoteTick"],
            bid=row["bestBid"],
            ask=row["bestAsk"],
            bidsize=row["bestBidSize"],
            asksize=row["bestAskSize"],
            time_tick=row["time"],
            log=log,
            fees=fees,
            depth=depth,
        )

    logger.info("Loaded exchange graph")
    return graph
