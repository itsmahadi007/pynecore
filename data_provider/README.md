# PyneCore Data Provider Plugin

A standalone Python package that provides data provider plugins for PyneCore. This package allows users to download historical OHLCV (Open, High, Low, Close, Volume) data from various sources and save it in PyneCore's binary OHLCV format for high-performance backtesting and analysis.

## Features

- **Modular Architecture**: Pluggable data providers with a common interface
- **Multiple Data Sources**: 
  - **CCXTProvider**: Access 100+ cryptocurrency exchanges via CCXT library
  - **CapitalComProvider**: Stocks, forex, indices, and commodities via Capital.com API
- **High-Performance Storage**: Data saved in PyneCore's optimized binary OHLCV format
- **Flexible Configuration**: TOML-based configuration with exchange-specific settings
- **Rich CLI Interface**: Command-line tools with progress bars and resume capability
- **Programmatic API**: Full Python API for integration into custom applications
- **Automatic Resume**: Smart resume functionality for interrupted downloads
- **Symbol Discovery**: List and search available symbols from each provider
- **Extensible Design**: Easy to add custom data providers

## Installation

```bash
# Basic installation
pip install pynecore-data-provider

# With CCXT support for cryptocurrency exchanges
pip install pynecore-data-provider[ccxt]

# With Capital.com support for stocks, forex, and indices
pip install pynecore-data-provider[capitalcom]

# With all providers
pip install pynecore-data-provider[ccxt,capitalcom]
```

## Usage

### Command Line Interface

The package provides a rich CLI interface via the `pyne-data` command:

```bash
# List available symbols for CCXT exchanges
pyne-data data download CCXTProvider dummy --list-symbols

# Download BTC/USDT data from Binance for the last 30 days
pyne-data data download CCXTProvider "binance:BTC/USDT" --timeframe D1 --from 30 --to 0

# Download with specific timeframes (1, 5, 15, 30 minutes; 60, 120, 240 minutes; 1D, 1W, 1M)
pyne-data data download CCXTProvider "bybit:BTC/USDT:USDT" --timeframe H1 --from 7 --to 0

# List available symbols for Capital.com
pyne-data data download CapitalComProvider dummy --list-symbols

# Download Apple stock data from Capital.com
pyne-data data download CapitalComProvider AAPL --timeframe D1 --from 30 --to 0

# Show detailed symbol information
pyne-data data download CCXTProvider "binance:BTC/USDT" --show-info

# Resume interrupted downloads (automatic detection)
pyne-data data download CCXTProvider "binance:BTC/USDT" --timeframe D1 --from 365 --to 0

# Truncate existing data and start fresh
pyne-data data download CCXTProvider "binance:BTC/USDT" --truncate --from 30 --to 0

# Specify custom directories
pyne-data data download CCXTProvider "binance:BTC/USDT" --ohlcv-dir ./my_data --config-dir ./my_config

# Use specific date ranges (YYYY-MM-DD format)
pyne-data data download CCXTProvider "binance:BTC/USDT" --from 2024-01-01 --to 2024-12-31
```

**Available Timeframes:**
- `1`, `5`, `10`, `15`, `30` (minutes)
- `60`, `120`, `240` (minutes = 1H, 2H, 4H)
- `D1` (daily), `W1` (weekly), `MN1` (monthly)

### Programmatic API

The package provides a clean Python API for integration into custom applications:

```python
from pynecore_data_provider.providers.ccxt import CCXTProvider
from pynecore_data_provider.providers.capitalcom import CapitalComProvider
from datetime import datetime, timedelta

# CCXT Provider example
ccxt_provider = CCXTProvider()

# Get symbol information
symbol_info = ccxt_provider.get_symbol_info("binance:BTC/USDT")
print(f"Symbol: {symbol_info.symbol}")
print(f"Exchange: {symbol_info.exchange}")
print(f"Base: {symbol_info.base}")
print(f"Quote: {symbol_info.quote}")
print(f"Available timeframes: {symbol_info.timeframes}")

# Download OHLCV data with context manager (recommended)
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

with ccxt_provider:
    ccxt_provider.download_ohlcv(
        symbol="binance:BTC/USDT",
        timeframe="D1",
        start_date=start_date,
        end_date=end_date
    )

# Capital.com Provider example
capitalcom_provider = CapitalComProvider()

# Get symbol information
symbol_info = capitalcom_provider.get_symbol_info("AAPL")
print(f"Symbol: {symbol_info.symbol}")
print(f"Name: {symbol_info.name}")
print(f"Market: {symbol_info.market}")

# Download OHLCV data
with capitalcom_provider:
    capitalcom_provider.download_ohlcv(
        symbol="AAPL",
        timeframe="D1",
        start_date=start_date,
        end_date=end_date
    )

# Discover available providers dynamically
from pynecore_data_provider.providers import discover_providers

available_providers = discover_providers()
for provider_name, provider_class in available_providers.items():
    print(f"Available provider: {provider_name} -> {provider_class}")
```

### Configuration

The package uses TOML configuration files for provider settings. Configuration files are automatically created in the `config` directory when you first use a provider.

#### CCXT Configuration

Configuration is stored in `config/ccxt_<EXCHANGE>_<SYMBOL>_<TIMEFRAME>.toml`:

```toml
[ccxt]
exchange = "binance"
symbol = "BTC/USDT"
timeframe = "D1"
api_key = ""  # Optional, for private endpoints
api_secret = ""  # Optional, for private endpoints
sandbox = false  # Set to true for testing
ratelimit = true  # Enable rate limiting

[ccxt.options]
# Exchange-specific options
adjustForTimeDifference = true
defaultType = "spot"  # spot, future, option, etc.
```

#### Capital.com Configuration

Configuration is stored in `config/capitalcom_<SYMBOL>_<TIMEFRAME>.toml`:

```toml
[capitalcom]
symbol = "AAPL"
timeframe = "D1"
api_key = "your_api_key"
password = "your_password"
identifier = "your_identifier"
base_url = "https://api-capital.backend-capital.com"  # Live trading URL
# base_url = "https://demo-api-capital.backend-capital.com"  # Demo URL

[capitalcom.options]
# Additional options
max_retries = 3
timeout = 30
```

#### Data Storage

OHLCV data is stored in binary format as `data/<provider>_<exchange>_<symbol>_<timeframe>.ohlcv` with corresponding TOML metadata files.

## Extending with Custom Providers

You can create custom data providers by inheriting from the base `Provider` class:

```python
from pynecore_data_provider.providers.provider import Provider
from pynecore_data_provider.models import SymbolInfo
from datetime import datetime
from typing import List, Dict, Any, Optional

class CustomProvider(Provider):
    def __init__(self, ohlcv_dir: str = "data", config_dir: str = "config"):
        super().__init__(ohlcv_dir=ohlcv_dir, config_dir=config_dir)
        # Initialize your custom provider
        self.api_client = None  # Your API client
    
    def __enter__(self):
        """Context manager entry - initialize connections"""
        # Initialize API connections, authenticate, etc.
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup connections"""
        # Cleanup connections
        pass
    
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Get detailed information about a symbol"""
        # Implement symbol information retrieval
        return SymbolInfo(
            symbol=symbol,
            name="Custom Symbol",
            exchange="custom",
            base="BASE",
            quote="QUOTE",
            timeframes=["1", "5", "15", "30", "60", "D1"],
            market="spot"
        )
    
    def get_list_of_symbols(self) -> List[str]:
        """Return list of available symbols"""
        # Fetch from your data source
        return ["SYMBOL1", "SYMBOL2", "SYMBOL3"]
    
    def download_ohlcv(self, symbol: str, timeframe: str, 
                      start_date: datetime, end_date: datetime,
                      progress_callback: Optional[callable] = None) -> None:
        """Download OHLCV data and save to PyneCore format"""
        # Fetch data from your source
        ohlcv_data = self._fetch_ohlcv_data(symbol, timeframe, start_date, end_date)
        
        # Save using parent class method
        self._save_ohlcv_data(symbol, timeframe, ohlcv_data)
    
    def _fetch_ohlcv_data(self, symbol: str, timeframe: str, 
                         start_date: datetime, end_date: datetime) -> List[List]:
        """Implement the actual data fetching from your source"""
        # Return data in format: [[timestamp_ms, open, high, low, close, volume], ...]
        # Timestamps should be in milliseconds since epoch
        return [
            [1640995200000, 47000.0, 48000.0, 46500.0, 47500.0, 1000.0],
            # ... more data
        ]
```

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# If you get import errors, ensure the package is installed:
pip install -e .

# For development with optional dependencies:
pip install -e ".[ccxt,capitalcom]"
```

**Timestamp Ordering Errors**
```bash
# If you get "Timestamps must be in chronological order" errors:
# This usually happens when existing data conflicts with new downloads
# Solution: Use --truncate flag to start fresh
pyne-data data download CCXTProvider "binance:BTC/USDT" --truncate --from 30 --to 0
```

**API Authentication Issues**
- Ensure your API credentials are correctly set in the TOML configuration files
- For Capital.com: Check that your identifier, API key, and password are valid
- For CCXT: Most public data doesn't require API keys, but some exchanges may have rate limits

**Exchange-Specific Issues**
- Some exchanges require specific symbol formats (e.g., "bybit:BTC/USDT:USDT" for Bybit perpetual futures)
- Use `--list-symbols` to see available symbols for each provider
- Use `--show-info` to get detailed symbol information

### Performance Tips

- Use appropriate timeframes for your needs (higher timeframes = faster downloads)
- Leverage the resume functionality for large historical downloads
- Use the `--truncate` flag only when necessary, as it deletes existing data
- Consider using custom `--ohlcv-dir` and `--config-dir` for better organization

## License

This project is licensed under the MIT License - see the LICENSE file for details.