#!/usr/bin/env python
"""Download BYBIT BTC/USDT data using CCXT provider programmatically."""

import sys
from pathlib import Path
from datetime import datetime, timedelta, UTC
import os

# Add the src directory to Python path for development
# First, try to add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

try:
    from pynecore_data_provider.providers.ccxt import CCXTProvider
except ImportError as e:
    print(f"❌ Error: Could not import pynecore_data_provider: {e}")
    print("Possible solutions:")
    print("1. Run: pip install -e . from the project root directory")
    print("2. Make sure you're in the correct directory")
    print("3. Check if the package is properly installed")
    sys.exit(1)


def download_bybit_btc_data():
    """Download BYBIT BTC/USDT data programmatically."""
    print("=== BYBIT BTC/USDT Data Download ===")
    
    # Check for existing data files and remove them to prevent timestamp conflicts
    data_dir = Path("./data")
    existing_files = list(data_dir.glob("ccxt_BYBIT_BTC_USDT_USDT_1D.*"))
    if existing_files:
        print(f"Found {len(existing_files)} existing data file(s). Removing to prevent conflicts...")
        for file in existing_files:
            try:
                os.remove(file)
                print(f"Removed: {file.name}")
            except Exception as e:
                print(f"Warning: Could not remove {file.name}: {e}")
    
    # Create CCXT provider instance with BYBIT symbol
    provider = CCXTProvider(
        symbol="BYBIT:BTC/USDT:USDT",
        timeframe="1D",
        ohlcv_dir=Path("./data"),  # Optional: specify data directory
        config_dir=Path("./config")  # Optional: specify config directory
    )
    
    # Get symbol information
    print("Getting symbol information...")
    try:
        sym_info = provider.get_symbol_info()
        if sym_info is None:
            print("Symbol info not found, updating...")
            sym_info = provider.update_symbol_info()
            provider.save_symbol_info(sym_info)
        
        print(f"Symbol: {sym_info.ticker}")
        print(f"Description: {sym_info.description}")
        print(f"Currency: {sym_info.currency}")
        print(f"Type: {sym_info.type}")
    except Exception as e:
        print(f"Error getting symbol info: {e}")
        return False
    
    # Define time range (30 days ago to now)
    from_date = datetime.now(UTC) - timedelta(days=30)
    to_date = datetime.now(UTC)
    
    print(f"\nDownloading data from {from_date.date()} to {to_date.date()}...")
    
    # Progress callback function
    def progress_callback(current_date):
        print(f"Progress: {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Download OHLCV data using context manager
    try:
        with provider as ohlcv_writer:
            provider.download_ohlcv(from_date, to_date, progress_callback)
        
        ohlcv_path = provider.ohlcv_path
        print(f"\n✅ Download complete! Data saved to: {ohlcv_path}")
        
        # Show file info
        if ohlcv_path.exists():
            file_size = ohlcv_path.stat().st_size
            print(f"File size: {file_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        print("\nPossible solutions:")
        print("1. Make sure you have CCXT installed: pip install pynecore-data-provider[ccxt]")
        print("2. Check your internet connection")
        print("3. Verify the symbol format is correct")
        print("4. Check if BYBIT API is accessible")
        return False


def main():
    """Main function."""
    print("PyneCore Data Provider - BYBIT BTC/USDT Download")
    print("=" * 50)
    
    # Create directories if they don't exist
    Path("./data").mkdir(exist_ok=True)
    Path("./config").mkdir(exist_ok=True)
    
    # Download data
    success = download_bybit_btc_data()
    
    if success:
        print("\n🎉 Data download completed successfully!")
    else:
        print("\n⚠️  Data download failed. Please check the error messages above.")
    
    print("\nNote: Make sure to configure providers.toml with your API credentials if needed.")


if __name__ == "__main__":
    main()