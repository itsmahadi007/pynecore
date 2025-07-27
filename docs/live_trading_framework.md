# Async Live Trading Framework Project

## Project Overview
This document outlines the context, goals, and acceptance criteria for developing an asynchronous live trading framework. The framework builds on PyneCore's existing data handling capabilities and is divided into stages, with Stage 1 as the current priority. The project will be implemented in a fresh directory structure within the workspace.

## Complete Context
- **Background**: PyneCore provides CLI tools for downloading OHLCV data from providers like CCXT (for cryptocurrencies) and Capital.com (for stocks, forex, indices). This is achieved through a modular and extensible architecture:
  - **Provider Abstraction**: PyneCore defines a `Provider` base class (`src/pynecore/providers/provider.py`) that all data providers extend. This class handles common functionalities like configuration loading (`providers.toml`), symbol information management, and saving OHLCV data to local files.
  - **CCXTProvider**: For cryptocurrency data, the `CCXTProvider` (`src/pynecore/providers/ccxt.py`) leverages the CCXT library to connect to various exchanges (e.g., Bybit). It uses `self._client.fetch_ohlcv` to retrieve historical OHLCV data, processes it, and then uses the base `Provider`'s `save_ohlcv_data` method to store it.
  - **CapitalComProvider**: For traditional financial markets (stocks, forex, indices), the `CapitalComProvider` (`src/pynecore/providers/capitalcom.py`) interacts with the Capital.com API. It defines specific timeframes and asset types (`SHARES`, `CURRENCIES`, `INDICES`) and implements methods like `get_market_details` and `get_historical_prices` to fetch data, which is then processed and saved similarly to CCXT data.
  - **Data Persistence**: All downloaded OHLCV data is transformed into PyneCore's standardized OHLCV format and saved locally as binary `.ohlcv` files (e.g., `ccxt_BYBIT_BTC_USDT_USDT_1D.ohlcv`). This is managed by the `save_ohlcv_data` method in the `Provider` base class, which utilizes `OHLCVWriter` (`src/pynecore/core/ohlcv_file.py`) for efficient file I/O.
  - **CLI Integration**: The `pyne data download` command (`src/pynecore/cli/commands/data.py`) dynamically loads the specified provider (e.g., `CCXTProvider` or `CapitalComProvider`) based on user input, initializes it with relevant parameters (symbol, timeframe, date range), and orchestrates the data download and saving process.
  Examples include:
  - `pyne data download ccxt --symbol "BYBIT:BTC/USDT:USDT" --timeframe 1D --from 30`
  - `pyne data download capitalcom --list-symbols --symbol "AAPL"`
- **Framework Requirements**: An async framework for live trading, supporting pluggable data providers that output to OHLCV files, integration with PyneCore for scripting/strategy execution, and data visualization plugins.
- **Stages**:
  - **Stage 1 (Priority)**: Data Provider Plugin – Configurable providers for live data streaming to OHLCV files.
  - **Stage 2**: PyneCore Integration – Use PyneCore for script execution on live data (already partially implemented).
  - **Stage 3**: Data Visualization Plugin – Tools to display and analyze data.
- **Technical Foundation**: Leverage PyneCore's `Provider` base class from `src/pynecore/providers/provider.py` for extensions. Use `asyncio` for asynchronous operations.
- **New Project Setup**: Start in a fresh directory (e.g., `/live_trading/` within the workspace) to avoid modifying core PyneCore files.

## Goals
- Develop a modular, async framework for live trading.
- Enable user-configurable data providers for real-time OHLCV data.
- Support custom provider implementations beyond the built-in CCXT and Capital.com providers.
- Create a simple, consistent API for implementing new data providers.
- Ensure seamless integration with PyneCore for strategy execution.
- Provide visualization tools for data monitoring.
- Maintain extensibility for additional providers and features.

## Implementation Architecture
- **Base Provider Interface**: Create an async version of PyneCore's `Provider` base class that defines the interface for all live data providers.
- **Provider Registry**: Implement a registry system that allows dynamic loading of providers based on configuration.
- **Custom Provider Support**: 
  - Define a clear interface with required methods that any custom provider must implement.
  - Provide a template/example for implementing custom providers.
  - Support configuration via TOML files similar to PyneCore's existing approach.
  - Allow providers to specify their capabilities (supported timeframes, symbols, etc.).
- **Built-in Providers**: 
  - Implement async versions of CCXT and Capital.com providers as reference implementations.
  - These will serve as examples for users creating their own custom providers.
- **Data Flow**: 
  - Providers fetch data asynchronously (polling or WebSocket).
  - Data is normalized to PyneCore's OHLCV format.
  - Normalized data is appended to `.ohlcv` files using the existing `OHLCVWriter`.

## Acceptance Criteria
- **Stage 1**:
  - Providers are pluggable and configurable via TOML files, allowing users to implement and use any data provider they want.
  - Framework includes built-in support for CCXT and Capital.com, but is designed to be extensible for any custom provider.
  - Async fetching of live data, appending to `.ohlcv` files without blocking.
  - Handles symbols, timeframes, and error conditions gracefully.
  - Tested with at least one crypto (e.g., BTC/USDT) and one stock (e.g., AAPL) symbol.
- **General**:
  - Code is clean, documented, and follows PyneCore's conventions.
  - Async operations use `asyncio` correctly (no sync blocking).
  - Framework runs without crashes on sample data.
  - Documentation includes setup, configuration, and usage examples.
- **Exclusions**: Real money trading execution; focus on data and simulation only. No UI beyond basic visualization in Stage 3.

## Next Steps
1. Create project directory structure.
2. Implement Stage 1 by extending PyneCore providers.
3. Create documentation and examples for implementing custom providers.
4. Test with both built-in and custom provider implementations.
5. Iterate based on testing results.