"""Main."""
import asyncio
from peregrinearb import (
    load_exchange_graph,
    print_profit_opportunity_for_path,
    bellman_ford,
)

graph = asyncio.get_event_loop().run_until_complete(load_exchange_graph("bitmart"))

paths = bellman_ford(graph)
for path in paths:
    print_profit_opportunity_for_path(graph, path)
