"""General Settings.

This prints the profit opportunities found in the graph for a single exchange.
"""
import math
import networkx as nx

__all__ = [
    "print_profit_opportunity_for_path",
]


def print_profit_opportunity_for_path(
    graph, path, round_to=10 ** -8, depth=False, starting_amount=100
):
    """Print profit opportunity for graph path."""
    if not path:
        return

    print("Starting with {} in {}".format(starting_amount, path[0]))

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
