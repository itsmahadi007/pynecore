#!/usr/bin/env python
"""Simple example showing programmatic usage of pynecore-data-provider.

This example demonstrates the most common use cases for using the package
programmatically in Python code, as shown in the README.
"""

from datetime import datetime, timedelta, UTC
from pathlib import Path

# Import providers directly from the package
try:
    from pynecore_data_provider import CCXTProvider, CapitalComProvider
except ImportError:
    # Fallback for development environment
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from pynecore_data_provider import CCXTProvider, CapitalComProvider


def example_ccxt_usage():
    """Example of using CCXTProvider programmatically."""
    print("=== CCXT Provider Example ===")
    
    # Create a CCXT provider instance
    ccxt_provider = CCXTProvider(
        symbol="binance:BTC/USDT",
        timeframe="1D",
        ohlcv_dir=Path("./data"),  # Optional
        config_dir=Path("./config")  # Optional
    )
    
    # Get symbol information
    print("Getting symbol information...")
    sym_info = ccxt_provider.get_symbol_info()
    if sym_info is None:
        sym_info = ccxt_provider.update_symbol_info()
        ccxt_provider.save_symbol_info(sym_info)
    
    print(f"Symbol: {sym_info.ticker}")
    print(f"Description: {sym_info.description}")
    print(f"Currency: {sym_info.currency}")
    print(f"Type: {sym_info.type}")
    
    # Define time range (last 7 days)
    from_date = datetime.now(UTC) - timedelta(days=7)
    to_date = datetime.now(UTC)
    
    # Progress callback function
    def progress_callback(current_date):
        print(f"Progress: {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Download OHLCV data
    print(f"Downloading data from {from_date.date()} to {to_date.date()}...")
    try:
        ccxt_provider.download_ohlcv(from_date, to_date, progress_callback)
        print(f"Download complete! Data saved to {ccxt_provider.get_ohlcv_path()}")
    except Exception as e:
        print(f"Error downloading data: {e}")


def example_capitalcom_usage():
    """Example of using CapitalComProvider programmatically."""
    print("\n=== Capital.com Provider Example ===")
    
    # Create a Capital.com provider instance
    capitalcom_provider = CapitalComProvider(
        symbol="AAPL",
        timeframe="1D",
        ohlcv_dir=Path("./data"),
        config_dir=Path("./config")
    )
    
    # List available symbols (first 10)
    print("Getting available symbols...")
    try:
        symbols = capitalcom_provider.get_list_of_symbols()
        print(f"Found {len(symbols)} symbols. First 10:")
        for symbol in symbols[:10]:
            print(f"  - {symbol}")
    except Exception as e:
        print(f"Error listing symbols: {e}")
        return
    
    # Get symbol information
    print(f"\nGetting symbol information for {capitalcom_provider.symbol}...")
    try:
        sym_info = capitalcom_provider.get_symbol_info()
        if sym_info is None:
            sym_info = capitalcom_provider.update_symbol_info()
            capitalcom_provider.save_symbol_info(sym_info)
        
        print(f"Symbol: {sym_info.ticker}")
        print(f"Description: {sym_info.description}")
        print(f"Currency: {sym_info.currency}")
        print(f"Type: {sym_info.type}")
    except Exception as e:
        print(f"Error getting symbol info: {e}")
        return
    
    # Define time range (last 30 days)
    from_date = datetime.now(UTC) - timedelta(days=30)
    to_date = datetime.now(UTC)
    
    # Progress callback function
    def progress_callback(current_date):
        print(f"Progress: {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Download OHLCV data
    print(f"Downloading data from {from_date.date()} to {to_date.date()}...")
    try:
        capitalcom_provider.download_ohlcv(from_date, to_date, progress_callback)
        print(f"Download complete! Data saved to {capitalcom_provider.get_ohlcv_path()}")
    except Exception as e:
        print(f"Error downloading data: {e}")


def example_discover_providers():
    """Example of discovering available providers."""
    print("\n=== Discovering Available Providers ===")
    
    try:
        from pynecore_data_provider import discover_providers, get_available_providers
    except ImportError:
        # Fallback for development environment
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from pynecore_data_provider import discover_providers, get_available_providers
    
    # Method 1: Using discover_providers
    providers = discover_providers()
    print(f"Available providers (discover_providers): {[p.__name__ for p in providers]}")
    
    # Method 2: Using get_available_providers
    providers2 = get_available_providers()
    print(f"Available providers (get_available_providers): {[p.__name__ for p in providers2]}")


def main():
    """Main function demonstrating all examples."""
    print("PyneCore Data Provider - Programmatic Usage Examples")
    print("=====================================================")
    
    # Create directories if they don't exist
    Path("./data").mkdir(exist_ok=True)
    Path("./config").mkdir(exist_ok=True)
    
    # Run examples
    example_discover_providers()
    
    try:
        example_ccxt_usage()
    except ImportError:
        print("\n=== CCXT Provider Example ===")
        print("CCXTProvider not available. Install with: pip install pynecore-data-provider[ccxt]")
    
    try:
        example_capitalcom_usage()
    except ImportError:
        print("\n=== Capital.com Provider Example ===")
        print("CapitalComProvider not available. Install with: pip install pynecore-data-provider[capitalcom]")
    
    print("\n=== Examples Complete ===")
    print("Note: Make sure to configure providers.toml with your API credentials before running.")


if __name__ == "__main__":
    main()