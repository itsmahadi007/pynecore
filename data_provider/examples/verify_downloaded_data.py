#!/usr/bin/env python3
"""
Verify Downloaded BYBIT BTC/USDT Data

This script verifies the downloaded OHLCV data and displays basic statistics.
"""

import sys
from pathlib import Path

# Add the src directory to Python path for development
try:
    from pynecore.core.ohlcv_file import OHLCVReader
    from pynecore.core.syminfo import SymInfo
except ImportError:
    # Fallback for development environment
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from pynecore.core.ohlcv_file import OHLCVReader
    from pynecore.core.syminfo import SymInfo


def verify_downloaded_data():
    """Verify and display information about downloaded BYBIT BTC/USDT data."""
    print("PyneCore Data Provider - Data Verification")
    print("==========================================")
    
    # File paths
    data_dir = Path("./data")
    ohlcv_file = data_dir / "ccxt_BYBIT_BTC_USDT_USDT_1D.ohlcv"
    symbol_info_file = data_dir / "ccxt_BYBIT_BTC_USDT_USDT_1D.toml"
    
    if not ohlcv_file.exists():
        print("❌ OHLCV data file not found. Please run the download script first.")
        return
    
    if not symbol_info_file.exists():
        print("❌ Symbol info file not found. Please run the download script first.")
        return
    
    print("=== Symbol Information ===")
    try:
        sym_info = SymInfo.load_toml(symbol_info_file)
        print(f"Symbol: {sym_info.ticker}")
        print(f"Description: {sym_info.description}")
        print(f"Currency: {sym_info.currency}")
        print(f"Type: {sym_info.type}")
        print(f"Timeframe: {sym_info.period}")
        print(f"Timezone: {sym_info.timezone}")
    except Exception as e:
        print(f"❌ Error reading symbol info: {e}")
        return
    
    print("\n=== OHLCV Data Statistics ===")
    try:
        with OHLCVReader(str(ohlcv_file)) as reader:
            print(f"Total candles: {reader.size}")
            print(f"File size: {ohlcv_file.stat().st_size} bytes")
            print(f"Start timestamp: {reader.start_timestamp}")
            print(f"Interval: {reader.interval} seconds")
            
            if reader.size > 0:
                # Read first and last candles
                candles = list(reader)
                first_candle = candles[0]
                last_candle = candles[-1]
                
                print(f"\n=== First Candle ===")
                print(f"Timestamp: {first_candle.timestamp}")
                print(f"Open: ${first_candle.open:,.2f}")
                print(f"High: ${first_candle.high:,.2f}")
                print(f"Low: ${first_candle.low:,.2f}")
                print(f"Close: ${first_candle.close:,.2f}")
                print(f"Volume: {first_candle.volume:,.2f}")
                
                print(f"\n=== Last Candle ===")
                print(f"Timestamp: {last_candle.timestamp}")
                print(f"Open: ${last_candle.open:,.2f}")
                print(f"High: ${last_candle.high:,.2f}")
                print(f"Low: ${last_candle.low:,.2f}")
                print(f"Close: ${last_candle.close:,.2f}")
                print(f"Volume: {last_candle.volume:,.2f}")
                
                # Calculate price statistics
                prices = [c.close for c in candles]
                min_price = min(prices)
                max_price = max(prices)
                avg_price = sum(prices) / len(prices)
                
                print(f"\n=== Price Statistics ===")
                print(f"Minimum price: ${min_price:,.2f}")
                print(f"Maximum price: ${max_price:,.2f}")
                print(f"Average price: ${avg_price:,.2f}")
                print(f"Price range: ${max_price - min_price:,.2f}")
                
                print("\n✅ Data verification completed successfully!")
                print(f"📊 Downloaded {reader.size} daily candles for BYBIT BTC/USDT")
            else:
                print("❌ No data found in the file")
                
    except Exception as e:
        print(f"❌ Error reading OHLCV data: {e}")
        return


if __name__ == "__main__":
    verify_downloaded_data()