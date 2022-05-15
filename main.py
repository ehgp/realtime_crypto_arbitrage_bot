"""Real Time Crypto Bot.

This is the main execution of Real Time Websocket Client to gather ticker bid/ask price and size.
Those tickers will be stored as rows in a SQLite database for analysis.py to output profitable trading opportunities
for trade.py to execute.

Currently two arbitrage models are being used:
1.Triangular Arbitrage.
2.Bellman Ford Optimization.
"""
import os
import yaml
from multiprocessing import Pool
import subprocess


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


# Multithreading
# def run_process(process):
#     """Run Process."""
#     os.system("python {}".format(process))

#         processes = ("kucoinlive.py",)
#         pool = Pool(processes=2)
#         pool.map(run_process, processes)


def main():
    """Execute Main."""
    if cf["exchange"] == "Kucoin":
        subprocess.run("python kucoinlive.py")
        # if cf["exchange"] == "Coinbase Pro":
        # subprocess.run("python coinbaselive.py")
        # if cf["exchange"] == "Gemini":
        # subprocess.run("python geminilive.py")


if __name__ == "__main__":
    cf = _load_config()
    main()
