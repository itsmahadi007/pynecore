"""CCXT provider for cryptocurrency exchanges.

This module provides the CCXTProvider class for downloading OHLCV data from
cryptocurrency exchanges using the CCXT library.
"""

from typing import Callable, Optional, Tuple, List, Dict, Any
import re
from datetime import datetime, UTC, timedelta, time
from pathlib import Path
import tomllib

from pynecore.core.syminfo import SymInfo, SymInfoInterval, SymInfoSession
from pynecore.types.ohlcv import OHLCV

from .provider import Provider

__all__ = ['CCXTProvider']

# Known limits for different exchanges
known_limits = {
    'binance': 1000,
    'bitmex': 500,
    'bybit': 200,
    'coinbase': 300,
    'kraken': 720,
    'kucoin': 1500,
    'okex': 200,
    'huobi': 2000,
}


def add_space_before_uppercase(s: str) -> str:
    """Add a space before each uppercase letter.

    Args:
        s: String to process

    Returns:
        Processed string
    """
    return re.sub(r'(?<!^)([A-Z])', r' \1', s)


class CCXTProvider(Provider):
    """CCXT provider for cryptocurrency exchanges."""

    config_keys = {
        '# Default settings for all exchanges if not specified': '',
        'apiKey': '',
        'secret': '',
        'password': '',
        '# ...anything else your exchange needs': '',
        '# Exchange specific configuration examples:': '',
        '# To set exchange specific configurations use sections like:': '',
        '# [ccxt.binance]': '',
        '# apiKey = "your_binance_api_key"': '',
        '# secret = "your_binance_secret"': '',
        '# ': '',
        '# [ccxt.kucoin]': '',
        '# apiKey = "your_kucoin_api_key"': '',
        '# secret = "your_kucoin_secret"': '',
        '# password = "your_kucoin_password"': '',
        '# ': '',
        '# [ccxt.okex]': '',
        '# apiKey = "your_okex_api_key"': '',
        '# secret = "your_okex_secret"': '',
        '# password = "your_okex_password"': '',
        '# isTestnet = true    # Add any custom parameter required by the exchange': ''
    }

    @classmethod
    def to_tradingview_timeframe(cls, timeframe: str) -> str:
        """Convert CCXT timeframe format to TradingView format.

        Args:
            timeframe: Timeframe in CCXT format (e.g. "1m", "5m", "1h", "1d")

        Returns:
            Timeframe in TradingView format (e.g. "1", "5", "60", "1D")

        Raises:
            ValueError: If timeframe format is invalid
        """
        if len(timeframe) < 2:
            raise ValueError(f"Invalid timeframe format: {timeframe}")

        unit = timeframe[-1]
        value = timeframe[:-1]

        # Verify that value is a valid number
        if not value.isdigit() or int(value) <= 0:
            raise ValueError(f"Invalid timeframe value: {value}")

        if unit == 'm':
            return value
        elif unit == 'h':
            return str(int(value) * 60)
        elif unit == 'd':
            return f"{value}D"
        elif unit == 'w':
            return f"{value}W"
        elif unit == 'M':
            return f"{value}M"
        else:
            raise ValueError(f"Invalid timeframe format: {timeframe}")

    @classmethod
    def to_exchange_timeframe(cls, timeframe: str) -> str:
        """Convert TradingView timeframe format to CCXT format.

        Args:
            timeframe: Timeframe in TradingView format (e.g. "1", "5", "60", "1D")

        Returns:
            Timeframe in CCXT format (e.g. "1m", "5m", "1h", "1d")

        Raises:
            ValueError: If timeframe format is invalid
        """
        if timeframe.isdigit():
            mins = int(timeframe)
            if mins <= 0:
                raise ValueError(f"Invalid timeframe value: {timeframe}")
            if mins >= 60 and mins % 60 == 0:
                return f"{mins // 60}h"
            return f"{mins}m"

        if len(timeframe) < 2:
            raise ValueError(f"Invalid timeframe format: {timeframe}")

        unit = timeframe[-1].upper()
        value = timeframe[:-1]

        # Verify that value is a valid number
        if not value.isdigit() or int(value) <= 0:
            raise ValueError(f"Invalid timeframe value: {value}")

        if unit == 'D':
            return f"{value}d"
        elif unit == 'W':
            return f"{value}w"
        elif unit == 'M':
            return f"{value}M"
        else:
            raise ValueError(f"Invalid timeframe format: {timeframe}")

    def __init__(self, *, symbol: Optional[str] = None, timeframe: Optional[str] = None,
                 ohlcv_dir: Optional[Path] = None, config_dir: Optional[Path] = None):
        """Initialize the CCXT provider.

        Args:
            symbol: The symbol to get data for (e.g. "BYBIT:BTC/USDT:USDT")
            timeframe: The timeframe to get data for in TradingView format
            ohlcv_dir: The directory to save OHLCV data
            config_dir: The directory to read the config file from
        """
        try:
            import ccxt
        except ImportError:
            raise ImportError("CCXT is not installed. Please install it using `pip install ccxt`")

        # Initialize parent class
        super().__init__(symbol=symbol, timeframe=timeframe, ohlcv_dir=ohlcv_dir, config_dir=config_dir)

        # Parse symbol format
        try:
            if symbol is None:
                raise ValueError("Error: Symbol not provided!")
            xchg, symbol = symbol.split(':', 1)
        except (ValueError, AttributeError):
            xchg = symbol
            symbol = None

        if not xchg:
            raise ValueError("Error: Exchange name not provided! Use 'exchange:symbol' format! "
                             "(or simple exchange, if you want to list symbols)")

        self.symbol = symbol
        exchange_name = xchg.lower()

        # Check if there's an exchange-specific configuration
        exchange_config = {}

        # Load configuration from providers.toml if config_dir is provided
        if config_dir:
            config_path = config_dir / 'providers.toml'
            if config_path.exists():
                with open(config_path, 'rb') as f:
                    data = tomllib.load(f)

                    # Look for exchange-specific config
                    exchange_section = f'ccxt.{exchange_name}'
                    if exchange_section in data:
                        exchange_config = data[exchange_section]
                    elif 'ccxt' in data:
                        # Use the default ccxt config
                        exchange_config = data['ccxt']

        # Create the CCXT client
        self._client: ccxt.Exchange = getattr(ccxt, exchange_name)({
            'enableRateLimit': True,
            'adjustForTimeDifference': True,
            **exchange_config
        })

    def get_list_of_symbols(self, *args, **kwargs) -> List[str]:
        """Get list of available symbols from the exchange.

        Returns:
            List of available symbols
        """
        self._client.load_markets()
        return self._client.symbols or []

    def get_opening_hours_and_sessions(self) -> Tuple[List[SymInfoInterval], List[SymInfoSession], List[SymInfoSession]]:
        """Get opening hours and sessions for cryptocurrency exchanges.

        Cryptocurrency exchanges are typically open 24/7.

        Returns:
            Tuple of (opening_hours, session_starts, session_ends)
        """
        opening_hours = []
        session_starts = []
        session_ends = []
        
        # 24/7 trading for all days of the week
        for i in range(7):
            opening_hours.append(
                SymInfoInterval(day=i, start=time(hour=0, minute=0), end=time(hour=23, minute=59, second=59)))
            session_starts.append(SymInfoSession(day=i, time=time(hour=0, minute=0)))
            session_ends.append(SymInfoSession(day=i, time=time(hour=23, minute=59, second=59)))

        return opening_hours, session_starts, session_ends

    def update_symbol_info(self) -> SymInfo:
        """Update symbol information from the exchange.

        Returns:
            Symbol information
        """
        self._client.load_markets()
        assert self._client.markets
        market_details = self._client.markets[self.symbol]

        # Get opening hours and sessions
        opening_hours, session_starts, session_ends = self.get_opening_hours_and_sessions()

        # Calculate minmove and pricescale from mintick
        mintick = market_details['precision']['price']
        minmove = mintick
        pricescale = 1
        while minmove < 1.0:
            pricescale *= 10
            minmove *= 10

        assert self._client.id
        return SymInfo(
            prefix=self._client.id.upper(),
            description=f"{market_details['base']} / {market_details['quote']} "
            f"{add_space_before_uppercase(market_details['info'].get('contractType', 'Spot'))}",
            ticker=market_details['info']['symbol'],
            currency=market_details['quote'],
            basecurrency=market_details['base'],
            period=self.timeframe,
            type="crypto",
            mintick=mintick,
            pricescale=pricescale,
            minmove=minmove,
            pointvalue=market_details.get('contractSize') or 1.0,
            timezone=self.timezone,
            opening_hours=opening_hours,
            session_starts=session_starts,
            session_ends=session_ends,
            # Additional information
            taker_fee=market_details.get('taker'),
            maker_fee=market_details.get('maker'),
        )

    def download_ohlcv(self, time_from: datetime, time_to: datetime,
                       on_progress: Optional[Callable[[datetime], None]] = None):
        """Download OHLCV data from the exchange.

        Args:
            time_from: The start time
            time_to: The end time
            on_progress: Optional callback to call on progress
        """
        # Shortcuts for the time_from and time_to
        tf: datetime = time_from.replace(tzinfo=None)
        tt: datetime = (time_to if time_to is not None else datetime.now(UTC)).replace(tzinfo=None)

        # Get the limit by exchange or use safe default
        assert self._client.id
        limit = known_limits.get(self._client.id, 100)

        # Collect all data first
        all_data = []
        
        try:
            # Loop through the time range
            while tf < tt:
                if on_progress:
                    on_progress(tf)

                # Fetch a part of data
                res: list = self._client.fetch_ohlcv(
                    symbol=self.symbol,
                    limit=limit,
                    timeframe=self.xchg_timeframe,
                    since=self._client.parse8601(tf.isoformat())
                )

                # If no data, skip to the next day, maybe the symbol was not yet traded that day
                if not res:
                    tf += timedelta(days=1)
                    continue

                # Add data to collection, filtering by time range
                for r in res:
                    t = int(r[0] / 1000)  # Convert milliseconds to seconds
                    dt = datetime.fromtimestamp(t, UTC).replace(tzinfo=None)
                    if dt > tt:
                        break
                    if dt >= time_from.replace(tzinfo=None):  # Only include data in our range
                        all_data.append(r)

                # Update tf to move to next batch
                if res:
                    last_ts = int(res[-1][0] / 1000)
                    tf = datetime.fromtimestamp(last_ts, UTC).replace(tzinfo=None)
                    # Add the timeframe interval to move to next batch
                    if self.xchg_timeframe and self.xchg_timeframe.endswith('d'):
                        tf += timedelta(days=int(self.xchg_timeframe[:-1]))
                    elif self.xchg_timeframe and self.xchg_timeframe.endswith('h'):
                        tf += timedelta(hours=int(self.xchg_timeframe[:-1]))
                    elif self.xchg_timeframe and self.xchg_timeframe.endswith('m'):
                        tf += timedelta(minutes=int(self.xchg_timeframe[:-1]))
                    else:
                        tf += timedelta(days=1)  # Default fallback
                else:
                    tf += timedelta(days=1)  # If no data, skip to next day

        except StopIteration:
            pass
        
        # Sort all data by timestamp and save
        all_data.sort(key=lambda x: x[0])
        
        # Remove duplicates (same timestamp)
        seen_timestamps = set()
        unique_data = []
        for r in all_data:
            if r[0] not in seen_timestamps:
                seen_timestamps.add(r[0])
                unique_data.append(r)
        
        # Save all data
        for r in unique_data:
            t = int(r[0] / 1000)  # Convert milliseconds to seconds
            ohlcv = OHLCV(
                timestamp=t,
                open=float(r[1]),
                high=float(r[2]),
                low=float(r[3]),
                close=float(r[4]),
                volume=float(r[5]),
            )
            self.save_ohlcv_data(ohlcv)

        if on_progress:
            on_progress(tt)