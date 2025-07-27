#!/usr/bin/env python
"""Example script for downloading OHLCV data using pynecore-data-provider.

This script demonstrates how to use the pynecore-data-provider package to download
OHLCV data from various providers programmatically.
"""

import argparse
import sys
from datetime import datetime, timedelta, UTC
from pathlib import Path

from pynecore_data_provider.utils import load_provider_class, discover_providers


def main():
    """Main entry point for the example script."""
    # Get available providers
    available_providers = discover_providers()
    provider_names = [p.__name__ for p in available_providers]
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Download OHLCV data using pynecore-data-provider")
    parser.add_argument(
        "provider",
        choices=provider_names,
        help="Provider to use for downloading data"
    )
    parser.add_argument(
        "symbol",
        help="Symbol to download data for"
    )
    parser.add_argument(
        "--timeframe", "-t",
        default="1D",
        help="Timeframe to download data for (e.g. 1, 5, 15, 60, 1D, 1W, 1M)"
    )
    parser.add_argument(
        "--from", "-f",
        dest="time_from",
        default="30",
        help="Start date (YYYY-MM-DD) or days ago"
    )
    parser.add_argument(
        "--to", "-to",
        dest="time_to",
        default="0",
        help="End date (YYYY-MM-DD) or days ago"
    )
    parser.add_argument(
        "--ohlcv-dir", "-o",
        type=Path,
        help="Directory to save OHLCV data"
    )
    parser.add_argument(
        "--config-dir", "-c",
        type=Path,
        help="Directory with providers.toml config"
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate existing OHLCV file"
    )
    
    args = parser.parse_args()
    
    # Load provider class
    try:
        provider_class = load_provider_class(args.provider)
    except ImportError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Parse dates
    if args.time_from.isdigit():
        from_date = datetime.now(UTC) - timedelta(days=int(args.time_from))
    else:
        try:
            from_date = datetime.fromisoformat(args.time_from)
        except ValueError:
            try:
                from_date = datetime.strptime(args.time_from, "%Y-%m-%d")
            except ValueError:
                print(f"Error: Invalid date format: {args.time_from}. Use YYYY-MM-DD or number of days ago.")
                sys.exit(1)
    
    if args.time_to.isdigit():
        to_date = datetime.now(UTC) - timedelta(days=int(args.time_to))
    else:
        try:
            to_date = datetime.fromisoformat(args.time_to)
        except ValueError:
            try:
                to_date = datetime.strptime(args.time_to, "%Y-%m-%d")
            except ValueError:
                print(f"Error: Invalid date format: {args.time_to}. Use YYYY-MM-DD or number of days ago.")
                sys.exit(1)
    
    # Create provider instance
    try:
        provider = provider_class(
            symbol=args.symbol,
            timeframe=args.timeframe,
            ohlcv_dir=args.ohlcv_dir,
            config_dir=args.config_dir
        )
    except Exception as e:
        print(f"Error creating provider: {e}")
        sys.exit(1)
    
    # Get symbol info
    print(f"Getting symbol info for {args.symbol}...")
    try:
        sym_info = provider.get_symbol_info()
        if sym_info is None:
            sym_info = provider.update_symbol_info()
            provider.save_symbol_info(sym_info)
    except Exception as e:
        print(f"Error getting symbol info: {e}")
        sys.exit(1)
    
    # Check if we need to truncate
    ohlcv_path = provider.get_ohlcv_path()
    if args.truncate and ohlcv_path.exists():
        print(f"Truncating {ohlcv_path}")
        try:
            ohlcv_path.unlink()
        except Exception as e:
            print(f"Error truncating file: {e}")
            sys.exit(1)
    
    # Download data
    print(f"Downloading {args.symbol} {args.timeframe} data from {from_date} to {to_date}...")
    
    # Progress callback
    def progress_callback(current_date):
        print(f"Progress: {current_date}")
    
    try:
        provider.download_ohlcv(from_date, to_date, progress_callback)
    except Exception as e:
        print(f"Error downloading data: {e}")
        sys.exit(1)
    
    print(f"Download complete! Data saved to {ohlcv_path}")


if __name__ == "__main__":
    main()