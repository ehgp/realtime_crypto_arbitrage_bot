# AGENTS.md -- Architecture + Repo Guidelines (Project: realtime_crypto_arbitrage_bot)

**Last updated**: 2026-04-09

## Scope
Cryptocurrency arbitrage bot implementing triangular arbitrage detection and execution across multiple exchanges (KuCoin, Coinbase Pro, Gemini). Uses Bellman-Ford algorithm for negative cycle detection in currency graphs. Includes analysis tooling, historical data tracking, and Docker-based deployment.

## Architecture Overview
```
realtime_crypto_arbitrage_bot/
  main.py                   # Application entry point
  bellmanford.py            # Bellman-Ford negative cycle detection
  analysis.py               # Market analysis engine
  trade.py                  # Trade execution logic
  triarb.py                 # Triangular arbitrage detection
  history.py                # Historical data tracking
  kucoinlive.py             # KuCoin exchange connector
  coinbaselive.py           # Coinbase Pro exchange connector
  geminilive.py             # Gemini exchange connector
  parameters.yaml           # Bot configuration parameters
  log_config.yaml           # Logging configuration
  requirements.txt
  Pipfile
  Dockerfile
  docker-compose.yml
  bib/                      # Bibliography / research references
  comparison/
    __init__.py
    Arbitrage-Bot/           # Reference implementation
    peregrine/               # Peregrine arbitrage library
  db/
    cbpro.db                # Coinbase Pro market data (SQLite)
    gemini.db                # Gemini market data (SQLite)
    kucoin.db                # KuCoin market data (SQLite)
    market.csv               # Market snapshots
    tri_arb_ops.csv          # Triangular arbitrage opportunities log
  docs/                      # Documentation
  eda/                       # Exploratory data analysis notebooks
  indicators/
    std_gauss_filter/        # Statistical filtering
  linters/                   # Code quality configs
  log/                       # Runtime logs
  presentation/              # Slide decks / presentations
  sql/                       # SQL scripts
  graph.png                  # Currency pair graph visualization
  execute_comparison.bat     # Windows execution script
  execute_comparison.sh      # Linux/Mac execution script
```

## Tech Stack
| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3 | Core application |
| Graph Algorithms | networkx | Bellman-Ford negative cycle detection |
| Data | pandas, numpy | Market data processing |
| KuCoin | kucoin-python | Exchange API client |
| Coinbase | cbpro | Coinbase Pro API client |
| Gemini | gemini-python | Gemini API client |
| Database | SQLAlchemy + aiosqlite | Async SQLite for market data persistence |
| Scraping | beautifulsoup4 | Web data extraction |
| Config | YAML | parameters.yaml, log_config.yaml |
| Containerization | Docker + Docker Compose | Self-hosted deployment |
| Package Management | Pipfile + requirements.txt | Dual dependency tracking |

## Known Constraints + Gotchas
1. `cbpro` (Coinbase Pro) API is deprecated -- Coinbase migrated to Advanced Trade API.
2. Exchange API keys required -- store in environment variables or parameters.yaml, never commit.
3. Multi-threaded execution -- race conditions possible in trade execution paths.
4. SQLite databases in `db/` contain historical market data -- can grow large.
5. `comparison/` contains third-party reference implementations (Arbitrage-Bot, peregrine) -- not original code.
6. Both `Pipfile` and `requirements.txt` exist -- keep in sync or pick one.
7. `execute_comparison.bat` and `.sh` -- cross-platform execution scripts for comparison analysis.

## Status
Dormant. Last commit: 2023-05-09.
