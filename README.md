#  Realtime Crypto Arbitrage Bot

Websockets implementation of real time arbitrage opportunity bot supporting [Kucoin](https://docs.kucoin.com/#general) currently.

Relies on four scripts:

* main:<br>
Main executable that will read the exchange chosen from parameters.yaml.

* *exchange*live
Websockets real time feed of price data depending on exchange, real time account and trade tracking (Kucoin only)

* trade:<br>
Trading module for execution of arbitrage trades.

* analysis:<br>
actual implementation of ML models.

1. Reverse and Forward Triangular Arbitrage in triarb.py
2. Bellman Ford Optimization in bellmanford.py

Features:<br>
Github CICD Pipeline<br>
SQLite implementation<br>
Docker containerization with docker compose<br>
Github Pages Sphinx Documentation

## Architecture

[![](/_static/Architecture.jpg)](https://github.com/ehgp/realtime_crypto_arbitrage_bot/blob/main/docs/source/_static/Architecture.jpg)<br>
**Figure 0** - Architecture

## Models

### Triangular Arbitrage
Our model was able to detect multiple trading opportunities in minutes with higher profit margin than 1%. Most opportunities have much higher profit than 1%. As you can see in the below image, the profit margins varies between 13% and 67%. The below image displays the pairs traded, trading size, trading price, forward arbitrage profit, and reverse arbitrage profit. Either forward arbitrage or reverse arbitrage shows ‘nan’ because whichever has higher profit the other is not considered as an opportunity.

[![](/_static/triangular-arbitrage-model-results.png)](https://github.com/ehgp/realtime_crypto_arbitrage_bot/blob/main/docs/source/_static/triangular-arbitrage-model-results.png)<br>
**Figure 1** - Triangular Arbitrage Model Results

### Bellman-Ford Algorithm

The Bellman–Ford algorithm calculates the shortest routes in a weighted digraph from a single source vertex to all other vertices. It is a versatile algorithm which is capable of hangling graphs. Some time the edge weights can be negative numbers. If the sum of the edges are negative, it means that they are reachable from the source. In this project, we used Bellman-Ford to detect arbitrage opportunities between different pairs. Our goal was to find the shortest trades to take advantage from the price discrepencies. Below image shows all the crypto currencies in Kucoin exchange with their trading pairs.

[![](/_static/graph.jpg)](https://github.com/ehgp/realtime_crypto_arbitrage_bot/blob/main/docs/source/_static/graph.png)<br>
**Figure 2** - Bellman Ford Graph

We tried to find other arbitrage opportunities than using only three pairs. Triangular arbitrage allowed us to trade three pairs by taking advantage of the price difference between them. In this section we traded multiple pairs and use the arbitrage opportunities between them. However, more trades mean more fees. Thus, the profit margin would go down when the number of trades increase. For that reason, Bellman-Ford is useful because it finds the shortest path. Below image shows a few of the results we got by using Bellman-Ford algorithm. The trade path, trade type, trade size, trade rates, and profit margin can be seen in the image. As it can be seen in the image, our model found 8 opportunities in 12 minutes. Some of the profit margins are higher than 50%. For some of them, the dollar profit is not that high due to price change in milliseconds on the pairs, and the fees applied to execute the trades.

[![](/_static/Bellman-Ford-Model-results.png)](https://github.com/ehgp/realtime_crypto_arbitrage_bot/blob/main/docs/source/_static/Bellman-Ford-Model-results.png)<br>
**Figure 3** - Bellman Ford Model Results

## Documentation

Documentation found [here](https://ehgp.github.io/realtime_crypto_arbitrage_bot/)

## Requirements

* Python 3.7
* Docker Desktop >= 4.5.1
* Pipenv 2022.1.8

## Installation

1. Fill out parameters.yaml

```yaml
KUCOIN_YOUR_API_KEY: ${KUCOIN_YOUR_API_KEY}
KUCOIN_YOUR_SECRET: ${KUCOIN_YOUR_SECRET}
KUCOIN_YOUR_PASS: ${KUCOIN_YOUR_PASS}
# trade.py parameters
fiat_cost_per_trade: 50.00
fiat_unit_per_trade: USD
# historical.py and forecasting.py parameters
url: "https://api.kucoin.com"
start_date: "2022-03-10 10:00:00"
end_date: "2022-03-10 10:05:00"
kline_type: "1min"
# Choose the exchange you want to run this on
exchange: 'Kucoin'
# taker fee in decimal
taker_fee: 0.001
# tri arb parameters
minimum_perc_tri_arb_profit: 0.1
```

2. If using Kucoin in production check the comment in line 168 in kucoinlive.py to enable private session.

## Usage

* To use docker you must have docker desktop available with docker compose and fill out credentials in .env:

* You can use either pipenv or your base python installation (default is requirements):<br>
Pipenv:<br>
pipenv install<br>
pipenv run python main.py

Requirements:<br>
pip install -r requirements.txt<br>
python main.py

## Authors

Erick Garcia<br>
Daniel Abbasi<br>
Yuksel Baris Dokuzoglu

## Disclosure

Use at your own risk and do your own research.<br>
Not responsible for lost funds.

## Support

We started this project as a capstone project with no profit taking.<br>
To continue this project development, support is heavily recommended and appreciated.<br>
We accept donations in multiple formats. Thank you.

## TODO

[Gemini](https://docs.gemini.com/rest-api/#sandbox) and [Coinbase](https://docs.cloud.coinbase.com/exchange/docs/sandbox) sandbox implementations.
1. Implementation of linear trading strategy
2. Get a trading module working with
