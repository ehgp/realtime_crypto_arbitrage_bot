"""Bellman Ford Graph Execution.

With an initialized networkx DiGraph DAG using our real time ticker data, execute Bellman Ford Optimization
to find most profitable trade path by finding the biggest negative weights in price and volume.
"""
import math
import networkx as nx
from utils import last_index_in_list
import logging
import logging.config
from pathlib import Path
import yaml
import os
import datetime as dt

__all__ = [
    "NegativeWeightFinder",
    "NegativeWeightDepthFinder",
    "bellman_ford_exec",
    "print_profit_opportunity_for_path",
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
        """Find arbitrage opportunities in self.graph and yields them.

        Args:
            source
                A node (currency) in self.graph. Opportunities will be yielded only if they are "reachable" from source.
                Reachable means that a series of trades can be executed to buy one of the currencies in the opportunity.
                For the most part, it does not matter what the value of source is, because typically any currency can be
                reached from any other via only a few trades.
            unique_paths : bool
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


def print_profit_opportunity_for_path(
    graph, path, round_to=8, depth=False, starting_amount=100
):
    """Print profit opportunity for graph path."""
    if not path:
        return

    print("Starting with {} in {}".format(starting_amount, path[0]))
    begin_amount = starting_amount
    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]

        if depth:
            volume = min(starting_amount, math.exp(-graph[start][end]["depth"]))
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
