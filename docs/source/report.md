# Report
## Abstract

The purpose of this study is to create an crypto arbitrage bot which allows users to execute automated trades. Triangular arbitrage is chosen as the arbitrage method, so the aim is to take advantage of the price differences between three different pairs. Kucoin, and Gemini are chosen exchanges for this project. The Bellman-Ford algorithm is used for decision making which computes the shortest path in a single source vortex. Other than triangular arbitrage, price prediction is done in this project for different coins' prices by using Sarimax, Autorima, and Nbeat models.

## Introduction

Arbirtrage is buying an asset on an exchange and selling it at another exchange for a higher price. It is a very straightforward process for traders. When a stock's price is lower on a foreign exchange, they buy it from there and sell it on the local exchange. The price on the foreign exchange is considered as "undervalued" because there are delays in adjusting the prices on different exchanges. However detecting arbitrage opportunities is a very hard work, taking advantage of them is even harder. Trading arbitrage opportunities manually is almost impossible because they occur and dissappear in seconds. For that reason, it requires advanced programs and computer equipments to automate this process. There are already numerous programs in every exchange which tries to take advantage from these discrepancies. There are different types of arbitrage like pure arbitrage, merger, arbitrage, triangular arbitrage, etc. In this project, triangular arbitrage is studied and applied in crypto market. If a disparity between three foreign currencies happens when their exchange rates do not exactly line up, resulting in triangular arbitrage. In other words, triangular arbitrage exploits market inefficiencies, and help market to become efficient. Below example shows how the triangular arbitrage works between the fiat currencies EUR, USD, and GBP.

**?Example for triangular arbitrage?** (This part is questionable. It might be useful because most people are not familiar with the concept of arbitrage)
_Suppose you have $1 million and you are provided with the following exchange rates: EUR/USD = 1.1586, EUR/GBP = 1.4600, and USD/GBP = 1.6939. With these exchange rates there is an arbitrage opportunity:_
_Sell dollars to buy euros: $1 million ÷ 1.1586 = €863,110_
_Sell euros for pounds: €863,100 ÷ 1.4600 = £591,171_
_Sell pounds for dollars: £591,171 x 1.6939 = $1,001,384_
_Subtract the initial investment from the final amount: $1,001,384 – $1,000,000 = $1,384_
_From these transactions, you would receive an arbitrage profit of $1,384 (assuming no transaction costs or taxes)._
_(Source: https://www.investopedia.com/terms/t/triangulararbitrage.asp)_

Triangular arbitrage is widely studied before from different aspects mostly in foreign exchange trading platforms. People practice triangular arbitrage between fiat currencies like the example above. While the analysis of Aloosh and Bekaert (2017) aims at controlling for the triangular arbitrage, our project try to charactrize and take advantage from arbitrage opportunities. Another research from Piccotti (2018) uses 5 minute period in his quote revisions, while our project tries to detect arbitrage opportunities in miliseconds. Speed is important while trading arbitrage, but in crypto world it is even more essential. The crypto market's volatility is extremely higher than foreign exchange market, thus working with shorter time intervals is essential.

In research from Gradojevic et al. (2020) it is found that high frequency traders' movements are supported by triangle arbitrage, which occurs in a milisecond trading environment. In their study, they found 80-100 arbitrage opportunities in a day. Expectedly, these aberrations are brief, lasting between 100 and 500 milliseconds. The average profit ranged between 0.5 and 0.75 basis points.








### What is Crypto Trading/Arbitrage Bot?

Trading bots are computer programs that are programmed to automatically execute buy and sell orders on an exchange based on a trading strategy. There are various service providers on the market not just for arbitrage but for trading too. Users can either choose an in-built trading strategy or make their own with their favorite indicators and currency pairs. Most of the trading bots are for trading, but couple of them offers arbitrage options too. Arbitrage bots have the same concept as the trading bots, but their strategy is based on making profit from price discrepencies. _For example Pionex is a crypto trading bot provider which also offers arbitrage bot. Their system is based on opening a hedge position in perpetual futures market on people's spot crypto positions. If a client has $1000 invested Ethereum (ETH) in spot, the bot opens a short position worth of $1000 on ETH-USDT pair. Since long position holders pay a funding fee to short position holders in every 8 hours, their earnings and losses balances each other but the earnings from funding fee is their profit. If the investors hold short positions more than the long positions, this strategy would not work. However, the funding rate (a ratio shows the balance between the long and short positions) is mostly positive, this strategy can make money to the investors especially in bullish market cycles._

Triangular arbitrage works in the same logic as in foreign exchange market. It exploits from the market inefficiencies in crypto market. Below example explains how it works:
.. image:: C:\Users\17179\Desktop\Capstone 606/Triangular crypto example.png
    :width: 400
    :alt: Example 1.A

## Dataset
Kucoin
Historical Data - Exploratory data analysis
Analysis.py - Live data

## Price Prediction with Time Series Analysis
Sarima
Arima
NBeat

## Bellman-Ford Algorithm
Analysis
Results

## Conclusion

## Referances

Aloosh, A., & Bekaert, G. (2017). Currency Factors. SSRN Electronic Journal. https://doi.org/10.2139/ssrn.3022623

Gradojevic, N., Erdemlioglu, D., & Gençay, R. (2020). A new wavelet-based ultra-high-frequency analysis of triangular currency arbitrage. Economic Modelling, 85, 57–73. https://doi.org/10.1016/j.econmod.2019.05.006

Piccotti, L. R. (2018). Jumps, cojumps, and efficiency in the spot foreign exchange market. Journal of Banking & Finance, 87, 49–67. https://doi.org/10.1016/j.jbankfin.2017.09.007

A new wavelet-based ultra-high-frequency analysis of triangular currency arbitrage
The microscopic relationships between triangular arbitrage and cross-currency correlations in a simple agent based model of foreign exchange markets
Detecting correlations and triangular arbitrage opportunities in the Forex by means of multifractal detrended cross-correlations analysis
https://www.geeksforgeeks.org/bellman-ford-algorithm-dp-23/