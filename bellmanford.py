"""Bellman Ford Graph Execution.

With an initialized networkx DiGraph DAG using our real time ticker data, execute Bellman Ford Optimization
to find most profitable trade path by finding the biggest negative weights in price and volume.
"""
import math
import networkx as nx
import logging
import logging.config
from pathlib import Path
import yaml
import os
import datetime as dt
import pandas as pd
import sqlite3

__all__ = [
    "NegativeWeightFinder",
    "NegativeWeightDepthFinder",
    "bellman_ford_exec",
    "print_profit_opportunity_for_path_store_db",
    "last_index_in_list",
    "load_exchange_graph",
    "draw_graph_to_png",
]


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
    config_path = os.path.join(os.path.abspath(path), "parameters.yaml")
    with open(config_path, "r") as config_file:
        config_defs = yaml.safe_load(config_file.read())

    if config_defs.values() is None:
        raise ValueError("parameters yaml file incomplete")

    return config_defs


cf = _load_config()


def last_index_in_list(li: list, element):
    """Thanks to https://stackoverflow.com/questions/6890170/how-to-find-the-last-occurrence-of-an-item-in-a-python-list."""
    return len(li) - next(i for i, v in enumerate(reversed(li), 1) if v == element)


class NegativeWeightFinder:
    """Negative Weight Finder."""

    __slots__ = ["graph", "predecessor_to", "distance_to", "seen_nodes"]

    def __init__(self, graph: nx.Graph):
        """Init."""
        self.graph = graph
        self.predecessor_to = {}
        # the maximum weight which can be transferred from source to each node
        self.distance_to = {}
        self.seen_nodes = set()

    def reset_all_but_graph(self):
        """Call this to look for opportunities after updating the graph."""
        self.predecessor_to = {}
        self.distance_to = {}
        self.seen_nodes = set()

    def initialize(self, source):
        """Initialize nodes."""
        for node in self.graph:
            # Initialize all distance_to values to infinity and all predecessor_to values to None
            self.distance_to[node] = float("Inf")
            self.predecessor_to[node] = None

        # The distance from any node to (itself) == 0
        self.distance_to[source] = 0

    def bellman_ford(self, source="BTC", unique_paths=True):
        """Find arbitrage opportunities in self graph and yields them.

        Args:
            source: A node (currency) in self.graph. Opportunities will be yielded only if they are "reachable" from source.
                Reachable means that a series of trades can be executed to buy one of the currencies in the opportunity.
                For the most part, it does not matter what the value of source is, because typically any currency can be
                reached from any other via only a few trades.
            unique_paths: If True, each opportunity is not yielded more than once

        Return:
            a generator of profitable (negatively-weighted) arbitrage paths in self.graph
        """
        logger.info("Running bellman_ford")
        self.initialize(source)

        logger.info("Relaxing edges")
        # After len(graph) - 1 passes, algorithm is complete.
        for i in range(len(self.graph) - 1):
            # for each node in the graph, test if the distance to each of its siblings is shorter by going from
            # source->base_currency + base_currency->quote_currency
            for edge in self.graph.edges(data=True):
                self.relax(edge)
        logger.info("Finished relaxing edges")

        for edge in self.graph.edges(data=True):
            if (
                self.distance_to[edge[0]] + edge[2]["weight"]
                < self.distance_to[edge[1]]
            ):
                if unique_paths and edge[1] in self.seen_nodes:
                    continue
                path = self._retrace_negative_cycle(edge[1], unique_paths)
                if path is None or path == (None, None):
                    continue
                yield path

        logger.info("Ran bellman_ford")

    def relax(self, edge):
        """Relax edges."""
        if self.distance_to[edge[0]] + edge[2]["weight"] < self.distance_to[edge[1]]:
            self.distance_to[edge[1]] = self.distance_to[edge[0]] + edge[2]["weight"]
            self.predecessor_to[edge[1]] = edge[0]

        return True

    def _retrace_negative_cycle(self, start, unique_paths):
        """Retraces an arbitrage opportunity (negative cycle).

        which a currency can reach and returns it.

        Parameters
        ----------
        start
            A node (currency) from which it is known an arbitrage opportunity is reachable
        unique_paths : bool
            unique_paths: If True, no duplicate opportunities are returned

        Returns
        -------
        list
            An arbitrage opportunity reachable from start. Value is None if seen_nodes is True and a
            duplicate opportunity would be returned.
        """
        arbitrage_loop = [start]
        prior_node = start
        while True:
            prior_node = self.predecessor_to[prior_node]
            # if negative cycle is complete
            if prior_node in arbitrage_loop:
                arbitrage_loop = arbitrage_loop[
                    : last_index_in_list(arbitrage_loop, prior_node) + 1
                ]
                arbitrage_loop.insert(0, prior_node)
                return arbitrage_loop

            # because if prior_node is in arbitrage_loop prior_node must be in self.seen_nodes. thus, this conditional
            # must proceed checking if prior_node is in arbitrage_loop
            if unique_paths and prior_node in self.seen_nodes:
                return None

            arbitrage_loop.insert(0, prior_node)
            self.seen_nodes.add(prior_node)


class NegativeWeightDepthFinder(NegativeWeightFinder):
    """Negative Weight Depth Finder."""

    def _retrace_negative_cycle(self, start, unique_paths):
        """Retraces an arbitrage opportunity (negative cycle).

        which a currency can reach and calculates the
        maximum amount of the first currency in the arbitrage opportunity that can be used to execute the opportunity.

        Parameters
        ----------
        start
            A node (currency) from which it is known an arbitrage opportunity is reachable
        unique_paths : bool`
            unique_paths: If True, no duplicate opportunities are returned

        Returns
        -------
        2-tuple
            [0] : list
                An arbitrage opportunity reachable from start. Value is None if seen_nodes is True and a
                duplicate opportunity would be returned.
            [1] : float
                The maximum amount of the first currency in the arbitrage opportunity that can be used to execute
                the opportunity. Value is None if seen_nodes is True and a duplicate opportunity would be returned.
        """
        arbitrage_loop = [start]
        prior_node = self.predecessor_to[arbitrage_loop[0]]
        # the minimum weight which can be transferred without being limited by edge depths
        minimum = self.graph[prior_node][arbitrage_loop[0]]["depth"]
        arbitrage_loop.insert(0, prior_node)
        while True:
            if arbitrage_loop[0] in self.seen_nodes and unique_paths:
                return None, None
            self.seen_nodes.add(prior_node)

            prior_node = self.predecessor_to[arbitrage_loop[0]]
            edge_weight = self.graph[prior_node][arbitrage_loop[0]]["weight"]
            edge_depth = self.graph[prior_node][arbitrage_loop[0]]["depth"]
            # if minimum is the limiting volume
            if edge_weight + edge_depth < minimum:
                minimum = max(minimum - edge_weight, edge_depth)
            # if edge_depth is the limiting volume
            elif edge_weight + edge_depth > minimum:
                minimum = edge_depth

            if prior_node in arbitrage_loop:
                arbitrage_loop = arbitrage_loop[
                    : last_index_in_list(arbitrage_loop, prior_node) + 1
                ]
                arbitrage_loop.insert(0, prior_node)
                logger.info("Retraced loop")
                return arbitrage_loop, math.exp(-minimum)

            arbitrage_loop.insert(0, prior_node)


def _add_weighted_edge_to_graph(
    graph: nx.DiGraph,
    base: str,
    quote: str,
    bid: float,
    ask: float,
    bidsize: float,
    asksize: float,
    time_tick: dt.datetime,
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
    # logger.info("Adding edge to graph")

    if fees:
        fee = cf["taker_fee"]
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

    # logger.info("Added edge to graph: %s" % (market_name))


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


def bellman_ford_exec(graph, source="BTC", unique_paths=True, depth=False):
    """Look at the docstring of the bellman_ford method in the NegativeWeightFinder class.

    (This is a static wrapper function.)
    If depth is true, yields all negatively weighted paths
    (accounting for depth) when starting with a weight of
    starting_amount.
    """
    if depth:
        return NegativeWeightDepthFinder(graph).bellman_ford(source, unique_paths)
    else:
        return NegativeWeightFinder(graph).bellman_ford(source, unique_paths)


def draw_graph_to_png(graph, to_file: str):
    """Draw graph to png."""
    nx.drawing.nx_pydot.to_pydot(graph).write_png(to_file)


def print_profit_opportunity_for_path_store_db(
    graph, path, round_to=8, depth=False, starting_amount=100
):
    """Print profit opportunity for graph path."""
    market_name_list = []
    trade_type_list = []
    sizes_list = []
    time_tick_list = []
    no_fee_rate_list = []
    if not path:
        return

    print("Starting with {} in {}".format(starting_amount, path[0]))
    begin_amount = starting_amount
    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]
        market_name_list.append(graph[start][end]["market_name"])
        trade_type_list.append(graph[start][end]["trade_type"])
        sizes_list.append(graph[start][end]["volume"])
        time_tick_list.append(graph[start][end]["time_tick"])
        no_fee_rate_list.append(graph[start][end]["no_fee_rate"])
        if depth:
            volume = round(
                min(starting_amount, math.exp(-graph[start][end]["depth"])), round_to
            )
            starting_amount = math.exp(-graph[start][end]["weight"]) * volume
        else:
            starting_amount *= math.exp(-graph[start][end]["weight"])

        rate = round(math.exp(-graph[start][end]["weight"]), round_to)
        resulting_amount = round(starting_amount, round_to)

        printed_line = "{} to {} at {} = {}".format(start, end, rate, resulting_amount)

        # todo: add a round_to option for depth
        if depth:
            printed_line += " with {} of {} traded".format(volume, start)

        print(printed_line)
    profit = format(resulting_amount - begin_amount, ".10f")
    profit_perc = format(((begin_amount / resulting_amount) - 1) * -100, ".2f")
    print("profit in %s: %s or %s %%" % (end, profit, profit_perc))
    df = [
        {
            "path": market_name_list,
            "trade_type": trade_type_list,
            "sizes": sizes_list,
            "rates": no_fee_rate_list,
            "profit": profit + " " + end,
            "profit_perc": profit_perc,
        }
    ]
    bf_profit_df = pd.DataFrame(df)
    con = sqlite3.connect("db/kucoin.db")
    cur = con.cursor()
    table = "bf_arb_ops"
    create_table = """CREATE TABLE IF NOT EXISTS bf_arb_ops \
(path text, trade_type text, sizes text, rates text, profit text, profit_perc text, \
attempted text, time text, UNIQUE (path, trade_type, sizes, rates) ON CONFLICT IGNORE)"""
    logger.info("Creating Table bf_arb_ops")
    cur.execute(create_table)
    con.commit()
    for i, row in bf_profit_df.iterrows():
        placeholders = ",".join('"' + str(e) + '"' for e in row)
        columns = ", ".join(bf_profit_df.columns)
        insert_table = "INSERT INTO %s ( %s, %s, %s ) VALUES ( %s, %s, %s )" % (
            table,
            columns,
            "attempted",
            "time",
            placeholders,
            '"N"',
            '"%s"' % (dt.datetime.now()),
        )
        logger.info("Inserting a row of data in %s" % (table))
        cur.execute(insert_table)
        con.commit()
    con.close()
