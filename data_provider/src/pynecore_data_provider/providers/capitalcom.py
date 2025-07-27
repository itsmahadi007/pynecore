"""Capital.com provider for stocks, forex, and indices.

This module provides the CapitalComProvider class for downloading OHLCV data from
Capital.com for stocks, forex, and indices.
"""

from typing import Callable, Optional, Tuple, List, Dict, Any, Union
import base64
import hashlib
import json
from datetime import datetime, UTC, timedelta, time
from pathlib import Path

from pynecore.core.syminfo import SymInfo, SymInfoInterval, SymInfoSession
from pynecore.types.ohlcv import OHLCV

from .provider import Provider

__all__ = ['CapitalComProvider']

# Timeframe mappings
TIMEFRAMES = {
    # Minutes
    '1': 'MINUTE',
    '5': 'MINUTE_5',
    '10': 'MINUTE_10',
    '15': 'MINUTE_15',
    '30': 'MINUTE_30',
    # Hours
    '60': 'HOUR',
    '120': 'HOUR_2',
    '240': 'HOUR_4',
    # Days and above
    '1D': 'DAY',
    '1W': 'WEEK',
    '1M': 'MONTH',
}

# Inverse mapping
TIMEFRAMES_INV = {v: k for k, v in TIMEFRAMES.items()}

# Asset types
TYPES = {
    'CURRENCIES': 'forex',
    'CRYPTOCURRENCIES': 'crypto',
    'SHARES': 'stock',
    'INDICES': 'index',
}


class CapitalComError(ValueError):
    """Exception raised for Capital.com API errors."""
    pass


class CapitalComProvider(Provider):
    """Capital.com provider for stocks, forex, and indices."""

    timezone = 'US/Eastern'
    config_keys = {
        '# If it is a demo account': '',
        'demo': False,
        '# These are required for Capital.com. You can get them from the Capital.com API settings.': '',
        'user_email': '',
        'api_key': '',
        'api_password': ''
    }

    @classmethod
    def to_tradingview_timeframe(cls, timeframe: str) -> str:
        """Convert Capital.com timeframe format to TradingView format.

        Args:
            timeframe: Timeframe in Capital.com format (e.g. "MINUTE", "MINUTE_5", "HOUR", "DAY")

        Returns:
            Timeframe in TradingView format (e.g. "1", "5", "60", "1D")

        Raises:
            ValueError: If timeframe format is invalid
        """
        try:
            return TIMEFRAMES_INV[timeframe.upper()]
        except KeyError:
            raise ValueError(f"Invalid Capital.com timeframe format: {timeframe}")

    @classmethod
    def to_exchange_timeframe(cls, timeframe: str) -> str:
        """Convert TradingView timeframe format to Capital.com format.

        Args:
            timeframe: Timeframe in TradingView format (e.g. "1", "5", "60", "1D")

        Returns:
            Timeframe in Capital.com format (e.g. "MINUTE", "MINUTE_5", "HOUR", "DAY")

        Raises:
            ValueError: If timeframe format is invalid
        """
        try:
            return TIMEFRAMES[timeframe]
        except KeyError:
            raise ValueError(f"Unsupported timeframe for Capital.com: {timeframe}")

    def __init__(self, *, symbol: Optional[str] = None, timeframe: Optional[str] = None,
                 ohlcv_dir: Optional[Path] = None, config_dir: Optional[Path] = None):
        """Initialize the Capital.com provider.

        Args:
            symbol: The symbol to get data for
            timeframe: The timeframe to get data for in TradingView format
            ohlcv_dir: The directory to save OHLCV data
            config_dir: The directory to read the config file from
        """
        super().__init__(symbol=symbol, timeframe=timeframe, ohlcv_dir=ohlcv_dir, config_dir=config_dir)
        self.security_token = None
        self.cst_token = None
        self.session_data = {}

    @staticmethod
    def encrypt_password(password: str) -> str:
        """Encrypt password for Capital.com API.

        Args:
            password: Plain text password

        Returns:
            Encrypted password
        """
        return base64.b64encode(hashlib.sha256(password.encode()).digest()).decode()

    def __call__(self, endpoint: str, *, data: Dict = None, method='post', _level=0) -> Union[Dict, List[Dict]]:
        """Call Capital.com API endpoints.

        Args:
            endpoint: API endpoint
            data: Request data
            method: HTTP method
            _level: Recursion level for handling authentication

        Returns:
            API response

        Raises:
            CapitalComError: If API returns an error
            ImportError: If httpx is not installed
        """
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx is not installed. Please install it using `pip install httpx`")

        # Check if we need to authenticate
        if _level == 0 and self.security_token is None and endpoint != 'session':
            self.create_session()

        # Prepare headers
        headers = {
            'X-CAP-API-KEY': self.config.get('api_key', ''),
        }

        # Add authentication headers if available
        if self.security_token is not None:
            headers['X-SECURITY-TOKEN'] = self.security_token
        if self.cst_token is not None:
            headers['CST'] = self.cst_token

        # Determine API URL based on demo setting
        is_demo = self.config.get('demo', False)
        base_url = 'https://demo-api-capital.backend-capital.com/' if is_demo else 'https://api-capital.backend-capital.com/'
        url = f"{base_url}api/v1/{endpoint}"

        # Make the request
        try:
            if method.lower() == 'get':
                response = httpx.get(url, headers=headers, params=data)
            else:  # post
                response = httpx.post(url, headers=headers, json=data)

            # Check for authentication headers in response
            if 'X-SECURITY-TOKEN' in response.headers:
                self.security_token = response.headers['X-SECURITY-TOKEN']
            if 'CST' in response.headers:
                self.cst_token = response.headers['CST']

            # Parse response
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json()
                error_msg = error_data.get('errorCode', 'Unknown error')
                if response.status_code == 401 and _level == 0:  # Unauthorized, try to re-authenticate
                    self.security_token = None
                    self.cst_token = None
                    return self.__call__(endpoint, data=data, method=method, _level=1)
                raise CapitalComError(f"API Error: {error_msg}")

        except httpx.RequestError as e:
            raise CapitalComError(f"Request Error: {str(e)}")
        except json.JSONDecodeError:
            raise CapitalComError(f"Invalid JSON response: {response.text}")

    def create_session(self):
        """Create a new session with Capital.com API."""
        if not self.config:
            raise CapitalComError("Capital.com configuration not found in providers.toml")

        if not all(k in self.config for k in ['user_email', 'api_key', 'api_password']):
            raise CapitalComError("Missing required configuration for Capital.com")

        # Create session
        response = self.__call__('session', data={
            'identifier': self.config['user_email'],
            'password': self.encrypt_password(self.config['api_password']),
        })

        self.session_data = response

    def get_list_of_symbols(self, *args, **kwargs) -> List[str]:
        """Get list of available symbols from Capital.com.

        Returns:
            List of available symbols
        """
        # Get markets
        response = self.__call__('markets', method='get')
        return [market['epic'] for market in response['markets']]

    def get_market_details(self, epic: str) -> Dict:
        """Get market details for a symbol.

        Args:
            epic: Symbol epic

        Returns:
            Market details
        """
        return self.__call__(f'markets/{epic}', method='get')

    def get_historical_prices(self, epic: str, resolution: str, from_date: datetime, to_date: datetime) -> List[Dict]:
        """Get historical prices for a symbol.

        Args:
            epic: Symbol epic
            resolution: Timeframe in Capital.com format
            from_date: Start date
            to_date: End date

        Returns:
            List of price data
        """
        # Format dates
        from_str = from_date.strftime('%Y-%m-%dT%H:%M:%S')
        to_str = to_date.strftime('%Y-%m-%dT%H:%M:%S')

        # Get prices
        response = self.__call__(
            f'prices/{epic}',
            method='get',
            data={
                'resolution': resolution,
                'from': from_str,
                'to': to_str,
                'max': 1000,  # Maximum number of candles
            }
        )

        return response['prices']

    def get_opening_hours_and_sessions(self) -> Tuple[List[SymInfoInterval], List[SymInfoSession], List[SymInfoSession]]:
        """Get opening hours and sessions for the symbol.

        Returns:
            Tuple of (opening_hours, session_starts, session_ends)
        """
        if not self.symbol:
            raise ValueError("Symbol not set")

        # Get market details
        market_details = self.get_market_details(self.symbol)

        opening_hours = []
        session_starts = []
        session_ends = []

        # Process opening hours
        if 'openingHours' in market_details and market_details['openingHours']:
            for oh in market_details['openingHours']['marketTimes']:
                day = int(oh['dayOfWeek'])
                
                # Parse times
                open_time = datetime.strptime(oh['openTime'], '%H:%M:%S').time()
                close_time = datetime.strptime(oh['closeTime'], '%H:%M:%S').time()
                
                opening_hours.append(SymInfoInterval(day=day, start=open_time, end=close_time))
                session_starts.append(SymInfoSession(day=day, time=open_time))
                session_ends.append(SymInfoSession(day=day, time=close_time))
        else:
            # Default to 24/7 for crypto
            for i in range(7):
                opening_hours.append(
                    SymInfoInterval(day=i, start=time(hour=0, minute=0), end=time(hour=23, minute=59, second=59)))
                session_starts.append(SymInfoSession(day=i, time=time(hour=0, minute=0)))
                session_ends.append(SymInfoSession(day=i, time=time(hour=23, minute=59, second=59)))

        return opening_hours, session_starts, session_ends

    def update_symbol_info(self) -> SymInfo:
        """Update symbol information from Capital.com.

        Returns:
            Symbol information
        """
        if not self.symbol:
            raise ValueError("Symbol not set")

        # Get market details
        market_details = self.get_market_details(self.symbol)

        # Get opening hours and sessions
        opening_hours, session_starts, session_ends = self.get_opening_hours_and_sessions()

        # Determine asset type
        instrument_type = market_details.get('instrumentType', '')
        asset_type = TYPES.get(instrument_type, 'stock')

        # Calculate mintick, pricescale, and minmove
        mintick = float(market_details.get('minNormalStopOrLimitDistance', 0.01))
        minmove = mintick
        pricescale = 1
        while minmove < 1.0:
            pricescale *= 10
            minmove *= 10

        # Create SymInfo
        return SymInfo(
            prefix='CAPITAL',
            description=market_details.get('instrumentName', self.symbol),
            ticker=self.symbol,
            currency=market_details.get('currencies', [{}])[0].get('code', 'USD'),
            basecurrency=market_details.get('currencies', [{}])[0].get('baseCode', ''),
            period=self.timeframe,
            type=asset_type,
            mintick=mintick,
            pricescale=pricescale,
            minmove=minmove,
            pointvalue=1.0,
            timezone=self.timezone,
            opening_hours=opening_hours,
            session_starts=session_starts,
            session_ends=session_ends,
            # Additional information
            avg_spread=float(market_details.get('spreadInfo', {}).get('value', 0)),
        )

    def download_ohlcv(self, time_from: datetime, time_to: datetime,
                       on_progress: Optional[Callable[[datetime], None]] = None):
        """Download OHLCV data from Capital.com.

        Args:
            time_from: The start time
            time_to: The end time
            on_progress: Optional callback to call on progress
        """
        if not self.symbol:
            raise ValueError("Symbol not set")
        if not self.xchg_timeframe:
            raise ValueError("Timeframe not set")

        # Shortcuts for the time_from and time_to
        tf: datetime = time_from.replace(tzinfo=None)
        tt: datetime = (time_to if time_to is not None else datetime.now(UTC)).replace(tzinfo=None)

        # Determine time chunk size based on timeframe
        if self.xchg_timeframe in ['MINUTE', 'MINUTE_5', 'MINUTE_10', 'MINUTE_15', 'MINUTE_30']:
            chunk_size = timedelta(days=7)  # 1 week for minute timeframes
        elif self.xchg_timeframe in ['HOUR', 'HOUR_2', 'HOUR_4']:
            chunk_size = timedelta(days=30)  # 1 month for hour timeframes
        else:
            chunk_size = timedelta(days=365)  # 1 year for day timeframes

        try:
            # Loop through the time range in chunks
            current_from = tf
            while current_from < tt:
                if on_progress:
                    on_progress(current_from)

                # Calculate chunk end time
                current_to = min(current_from + chunk_size, tt)

                # Fetch data for the current chunk
                prices = self.get_historical_prices(
                    epic=self.symbol,
                    resolution=self.xchg_timeframe,
                    from_date=current_from,
                    to_date=current_to
                )

                # If no data, skip to the next chunk
                if not prices:
                    current_from = current_to
                    continue

                # Process the data
                for price in prices:
                    # Parse timestamp
                    dt = datetime.fromisoformat(price['snapshotTime'].replace('Z', '+00:00'))
                    timestamp = int(dt.timestamp())

                    # Create OHLCV object
                    ohlcv = OHLCV(
                        timestamp=timestamp,
                        open=float(price['openPrice']['bid']),
                        high=float(price['highPrice']['bid']),
                        low=float(price['lowPrice']['bid']),
                        close=float(price['closePrice']['bid']),
                        volume=float(price.get('lastTradedVolume', 0)),
                    )

                    # Save data
                    self.save_ohlcv_data(ohlcv)

                # Move to the next chunk
                current_from = current_to

        except Exception as e:
            raise CapitalComError(f"Error downloading OHLCV data: {str(e)}")

        if on_progress:
            on_progress(tt)