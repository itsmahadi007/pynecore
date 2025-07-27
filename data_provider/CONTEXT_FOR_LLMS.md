# PyneCore Data Provider - Complete Context for LLMs

This document provides comprehensive technical context about the PyneCore Data Provider project for Large Language Models (LLMs) to understand the complete architecture, implementation details, and usage patterns.

## Project Overview

The PyneCore Data Provider is a standalone Python package that serves as a plugin system for downloading historical OHLCV (Open, High, Low, Close, Volume) data from various financial data sources. It's designed to integrate with the PyneCore backtesting framework but can be used independently.

### Key Characteristics
- **Modular Architecture**: Plugin-based system with a common Provider interface
- **High-Performance Storage**: Uses PyneCore's optimized binary OHLCV format
- **Multiple Data Sources**: Currently supports CCXT (crypto) and Capital.com (traditional markets)
- **Rich CLI and API**: Both command-line and programmatic interfaces
- **Configuration Management**: TOML-based configuration with automatic file generation
- **Resume Capability**: Smart resume functionality for interrupted downloads
- **Context Manager Support**: Proper resource management with Python context managers

## Project Structure

```
data_provider/
├── src/pynecore_data_provider/
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point
│   ├── main.py                  # Main CLI application
│   ├── data.py                  # Data download commands
│   ├── models.py                # Data models (SymbolInfo, etc.)
│   └── providers/
│       ├── __init__.py          # Provider discovery and enums
│       ├── provider.py          # Base Provider abstract class
│       ├── ccxt.py             # CCXT provider implementation
│       └── capitalcom.py       # Capital.com provider implementation
├── examples/
│   ├── simple_usage.py         # Programmatic usage examples
│   └── download_bybit_data.py  # Specific BYBIT download script
├── data/                       # Default OHLCV data storage
├── config/                     # Default configuration storage
├── pyproject.toml             # Project configuration and dependencies
└── README.md                  # User documentation
```

## Core Architecture

### Base Provider Class

Location: `src/pynecore_data_provider/providers/provider.py`

The `Provider` class is an abstract base class that defines the interface all data providers must implement:

```python
class Provider(ABC):
    def __init__(self, ohlcv_dir: str = "data", config_dir: str = "config"):
        # Base initialization with directory configuration
    
    @abstractmethod
    def __enter__(self):
        # Context manager entry - for resource initialization
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Context manager exit - for cleanup
    
    @abstractmethod
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        # Get detailed symbol information
    
    @abstractmethod
    def get_list_of_symbols(self) -> List[str]:
        # List all available symbols
    
    @abstractmethod
    def download_ohlcv(self, symbol: str, timeframe: str, 
                      start_date: datetime, end_date: datetime,
                      progress_callback: Optional[callable] = None) -> None:
        # Download and save OHLCV data
```

### Provider Implementations

#### CCXTProvider
Location: `src/pynecore_data_provider/providers/ccxt.py`

- **Purpose**: Provides access to 100+ cryptocurrency exchanges via the CCXT library
- **Symbol Format**: `"exchange:base/quote"` or `"exchange:base/quote:settle"` for derivatives
- **Key Features**:
  - Automatic exchange initialization and rate limiting
  - Support for spot, futures, and options markets
  - Configurable timeframes and exchange-specific options
  - Robust error handling and retry logic
  - Data deduplication and chronological sorting

#### CapitalComProvider
Location: `src/pynecore_data_provider/providers/capitalcom.py`

- **Purpose**: Provides access to stocks, forex, indices, and commodities via Capital.com API
- **Symbol Format**: Standard symbol names (e.g., "AAPL", "EURUSD")
- **Key Features**:
  - OAuth2 authentication with automatic token refresh
  - Support for multiple asset classes
  - Market hours awareness
  - Demo and live API support

### Data Models

Location: `src/pynecore_data_provider/models.py`

#### SymbolInfo
Contains comprehensive symbol metadata:
- `symbol`: Symbol identifier
- `name`: Human-readable name
- `exchange`: Exchange or provider name
- `base`: Base currency/asset
- `quote`: Quote currency/asset
- `timeframes`: Available timeframes list
- `market`: Market type (spot, future, option, etc.)
- Additional provider-specific fields

### Configuration System

The package uses TOML files for configuration, automatically generated per symbol/timeframe combination:

#### CCXT Configuration Pattern
`config/ccxt_<EXCHANGE>_<SYMBOL>_<TIMEFRAME>.toml`

```toml
[ccxt]
exchange = "binance"
symbol = "BTC/USDT"
timeframe = "D1"
api_key = ""
api_secret = ""
sandbox = false
ratelimit = true

[ccxt.options]
adjustForTimeDifference = true
defaultType = "spot"
```

#### Capital.com Configuration Pattern
`config/capitalcom_<SYMBOL>_<TIMEFRAME>.toml`

```toml
[capitalcom]
symbol = "AAPL"
timeframe = "D1"
api_key = "your_api_key"
password = "your_password"
identifier = "your_identifier"
base_url = "https://api-capital.backend-capital.com"

[capitalcom.options]
max_retries = 3
timeout = 30
```

### Data Storage Format

OHLCV data is stored in PyneCore's binary format:
- **File Pattern**: `data/<provider>_<exchange>_<symbol>_<timeframe>.ohlcv`
- **Metadata**: Corresponding `.toml` files with symbol information
- **Format**: Binary format optimized for fast reading in backtesting
- **Data Structure**: [timestamp_ms, open, high, low, close, volume] arrays

## CLI Interface

Entry Point: `pyne-data` command (defined in `pyproject.toml`)

### Command Structure
```bash
pyne-data data download <PROVIDER> <SYMBOL> [OPTIONS]
```

### Key CLI Features
- **Provider Selection**: Dynamic enumeration of available providers
- **Symbol Management**: List symbols, show detailed info
- **Flexible Date Ranges**: Support for relative days and absolute dates
- **Progress Tracking**: Rich progress bars with ETA
- **Resume Capability**: Automatic detection and resumption of interrupted downloads
- **Data Management**: Truncate existing data, custom directories

### CLI Implementation Details

Location: `src/pynecore_data_provider/data.py`

- Uses `typer` for CLI framework
- Dynamic provider enumeration via `AvailableProvidersEnum`
- Rich console output with progress bars
- Comprehensive error handling and user feedback
- Support for both interactive and scripted usage

## Programmatic API

### Basic Usage Pattern
```python
from pynecore_data_provider.providers.ccxt import CCXTProvider
from datetime import datetime, timedelta

# Initialize provider
provider = CCXTProvider()

# Use context manager for proper resource management
with provider:
    # Get symbol information
    symbol_info = provider.get_symbol_info("binance:BTC/USDT")
    
    # Download data
    provider.download_ohlcv(
        symbol="binance:BTC/USDT",
        timeframe="D1",
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )
```

### Provider Discovery
```python
from pynecore_data_provider.providers import discover_providers

available_providers = discover_providers()
for name, provider_class in available_providers.items():
    print(f"{name}: {provider_class}")
```

## Dependencies and Installation

### Core Dependencies
- `pynesys-pynecore`: Core PyneCore framework for OHLCV handling
- `typer`: CLI framework
- `rich`: Rich console output and progress bars
- `toml`: Configuration file handling

### Optional Dependencies
- `ccxt`: For CCXTProvider (cryptocurrency exchanges)
- `requests`: For CapitalComProvider (HTTP API client)

### Installation Patterns
```bash
# Basic installation
pip install -e .

# With all optional dependencies
pip install -e ".[ccxt,capitalcom]"

# Development installation
pip install -e ".[dev]"
```

## Error Handling and Troubleshooting

### Common Issues

1. **Timestamp Ordering Errors**
   - Cause: Existing data conflicts with new downloads
   - Solution: Use `--truncate` flag or delete existing files
   - Prevention: Automatic file cleanup in download scripts

2. **Import Errors**
   - Cause: Missing optional dependencies or incorrect Python path
   - Solution: Install with appropriate optional dependencies
   - Development: Use editable installation with proper path setup

3. **API Authentication Issues**
   - Cause: Invalid or missing API credentials
   - Solution: Verify TOML configuration files
   - Debug: Check API endpoint URLs and credential formats

4. **Exchange-Specific Symbol Formats**
   - Cause: Different exchanges use different symbol conventions
   - Solution: Use `--list-symbols` and `--show-info` for discovery
   - Examples: "bybit:BTC/USDT:USDT" vs "binance:BTC/USDT"

### Debugging Strategies

1. **Use CLI for Testing**: Start with CLI commands before programmatic usage
2. **Check Configuration**: Verify TOML files are correctly generated
3. **Symbol Discovery**: Always use provider-specific symbol listing
4. **Progress Monitoring**: Use progress callbacks for long downloads
5. **Context Managers**: Always use `with` statements for proper cleanup

## Extension Points

### Creating Custom Providers

1. **Inherit from Provider**: Implement all abstract methods
2. **Context Management**: Implement `__enter__` and `__exit__`
3. **Symbol Information**: Return comprehensive `SymbolInfo` objects
4. **Data Format**: Return OHLCV data as `[[timestamp_ms, o, h, l, c, v], ...]`
5. **Error Handling**: Implement robust error handling and retries
6. **Configuration**: Use TOML files for provider-specific settings

### Integration with PyneCore

- OHLCV files are directly compatible with PyneCore backtesting framework
- Binary format provides optimal performance for large datasets
- Metadata files enable symbol discovery and validation
- Configuration system supports multiple environments (demo/live)

## Performance Considerations

### Optimization Strategies

1. **Timeframe Selection**: Higher timeframes = faster downloads
2. **Batch Processing**: Download multiple symbols in sequence
3. **Resume Capability**: Leverage existing data when possible
4. **Rate Limiting**: Respect exchange rate limits to avoid bans
5. **Data Deduplication**: Automatic removal of duplicate timestamps
6. **Memory Management**: Stream processing for large datasets

### Scalability Features

- **Parallel Downloads**: Multiple providers can run concurrently
- **Incremental Updates**: Resume from last downloaded timestamp
- **Storage Efficiency**: Binary format minimizes disk usage
- **Configuration Caching**: Reuse provider configurations

## Security Considerations

### API Key Management
- Store credentials in TOML configuration files
- Support for both demo and live API endpoints
- Never log or expose API credentials
- Use environment variables for sensitive deployments

### Data Integrity
- Timestamp validation and chronological ordering
- Data deduplication to prevent corruption
- Atomic file operations to prevent partial writes
- Backup and recovery strategies for critical data

## Future Development Directions

### Planned Enhancements
1. **Additional Providers**: More data sources (Alpha Vantage, Yahoo Finance, etc.)
2. **Real-time Data**: WebSocket support for live data feeds
3. **Data Validation**: Enhanced data quality checks and anomaly detection
4. **Caching Layer**: Redis/SQLite caching for frequently accessed data
5. **Monitoring**: Health checks and performance metrics
6. **Cloud Storage**: S3/GCS integration for distributed deployments

### Architecture Evolution
- **Plugin System**: Dynamic provider loading and registration
- **Event System**: Hooks for data processing and validation
- **Microservices**: Containerized deployment options
- **API Gateway**: RESTful API for remote data access

This context document provides LLMs with comprehensive understanding of the PyneCore Data Provider architecture, implementation patterns, usage scenarios, and extension points for effective assistance with development, debugging, and enhancement tasks.