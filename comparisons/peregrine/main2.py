"""Main2."""
from peregrinearb import (
    create_weighted_multi_exchange_digraph,
    bellman_ford_multi,
    print_profit_opportunity_for_path_multi,
)


graph = create_weighted_multi_exchange_digraph(
    ["exmo", "binance", "bitmex", "bittrex", "gemini", "kraken"], log=True
)


graph, paths = bellman_ford_multi(graph, "ETH", unique_paths=True)
for path in paths:
    print_profit_opportunity_for_path_multi(graph, path)
