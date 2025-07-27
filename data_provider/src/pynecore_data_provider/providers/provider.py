"""Base Provider class for all data providers.

This module defines the Provider base class that all data providers must extend.
It handles common functionalities like configuration loading, symbol information management,
and saving OHLCV data to local files.
"""

from typing import Callable, Optional, Tuple, List, Dict, Any, Union
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime, time
import tomllib

from pynecore.types.ohlcv import OHLCV
from pynecore.core.syminfo import SymInfo, SymInfoInterval, SymInfoSession
from pynecore.core.ohlcv_file import OHLCVWriter, OHLCVReader


class Provider(ABC):
    """Base class for all data providers."""

    timezone = 'UTC'
    """Timezone of the provider."""

    symbol: Optional[str] = None
    """Symbol of the provider."""

    timeframe: Optional[str] = None
    """Timeframe of the provider in TradingView format."""

    xchg_timeframe: Optional[str] = None
    """Exchange-specific timeframe format."""

    ohlcv_path: Optional[Path] = None
    """Path to save OHLCV data."""

    config_keys: Dict[str, Any] = {
        '# Settings for the provider': '',
    }
    """Key-value pairs to put into providers.toml, if key starts with '#' it is a comment."""

    config: Dict[str, Any] = {}
    """Config dict for the provider loaded from providers.toml."""

    @classmethod
    @abstractmethod
    def to_tradingview_timeframe(cls, timeframe: str) -> str:
        """Convert provider-specific timeframe to TradingView format.

        Args:
            timeframe: Timeframe in provider-specific format

        Returns:
            Timeframe in TradingView format

        Raises:
            ValueError: If timeframe format is invalid
        """
        pass

    @classmethod
    @abstractmethod
    def to_exchange_timeframe(cls, timeframe: str) -> str:
        """Convert TradingView timeframe to provider-specific format.

        Args:
            timeframe: Timeframe in TradingView format

        Returns:
            Timeframe in provider-specific format

        Raises:
            ValueError: If timeframe format is invalid
        """
        pass

    @classmethod
    def get_ohlcv_path(cls, symbol: str, timeframe: str, ohlcv_dir: Path, provider_name: Optional[str] = None) -> Path:
        """Get the output path for the OHLCV data file.

        Args:
            symbol: The symbol to get data for
            timeframe: The timeframe in TradingView format
            ohlcv_dir: The directory to save OHLCV data
            provider_name: Optional provider name, defaults to lowercase class name

        Returns:
            Path to the OHLCV data file
        """
        return ohlcv_dir / (f"{provider_name or cls.__name__.lower().replace('provider', '')}"
                           f"_{symbol.replace('/', '_').replace(':', '_')}"
                           f"_{timeframe}.ohlcv")

    def __init__(self, *, symbol: Optional[str] = None, timeframe: Optional[str] = None,
                 ohlcv_dir: Optional[Path] = None, config_dir: Optional[Path] = None):
        """Initialize the provider.

        Args:
            symbol: The symbol to get data for
            timeframe: The timeframe to get data for in TradingView format
            ohlcv_dir: The directory to save OHLCV data
            config_dir: The directory to read the config file from
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.xchg_timeframe = self.to_exchange_timeframe(timeframe) if timeframe else None
        self.ohlcv_path = self.get_ohlcv_path(symbol, timeframe, ohlcv_dir) if ohlcv_dir and symbol and timeframe else None
        self.ohlcv_file = OHLCVWriter(self.ohlcv_path) if self.ohlcv_path else None

        if not config_dir and ohlcv_dir:  # Default config dir from the parent of the ohlcv_dir
            config_dir = ohlcv_dir.parent / 'config'
        self.config_dir = config_dir

        if config_dir:
            self.load_config()

    def __enter__(self) -> OHLCVWriter:
        """Context manager entry."""
        if self.ohlcv_file is None:
            raise ValueError("OHLCV file not initialized")
        return self.ohlcv_file.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.ohlcv_file is not None:
            self.ohlcv_file.close()

    @abstractmethod
    def get_list_of_symbols(self, *args, **kwargs) -> List[str]:
        """Get list of available symbols from the provider.

        Returns:
            List of available symbols
        """
        pass

    def load_config(self):
        """Load configuration from providers.toml."""
        if self.config_dir is None:
            return
            
        config_path = self.config_dir / 'providers.toml'
        if not config_path.exists():
            return
            
        with open(config_path, 'rb') as f:
            data = tomllib.load(f)
            provider_name = self.__class__.__name__.replace('Provider', '').lower()
            if provider_name in data:
                self.config = data[provider_name]

    @abstractmethod
    def update_symbol_info(self) -> SymInfo:
        """Update symbol information from the provider.

        Returns:
            Symbol information
        """
        pass

    def is_symbol_info_exists(self) -> bool:
        """Check if symbol information file exists.

        Returns:
            True if symbol information file exists, False otherwise
        """
        if self.ohlcv_path is None:
            return False
        return self.ohlcv_path.with_suffix('.toml').exists()

    def get_symbol_info(self, force_update: bool = False) -> SymInfo:
        """Get symbol information.

        Args:
            force_update: Force update the symbol information

        Returns:
            Symbol information
        """
        if self.ohlcv_path is None:
            raise ValueError("OHLCV path not initialized")
            
        toml_path = self.ohlcv_path.with_suffix('.toml')
        
        # Check if file already exists
        if self.is_symbol_info_exists() and not force_update:
            return SymInfo.load_toml(toml_path)

        sym_info = self.update_symbol_info()
        sym_info.save_toml(toml_path)
        return sym_info

    @abstractmethod
    def get_opening_hours_and_sessions(self) -> Tuple[List[SymInfoInterval], List[SymInfoSession], List[SymInfoSession]]:
        """Get opening hours and sessions of a symbol.

        Returns:
            Tuple of (opening_hours, session_starts, session_ends)
        """
        pass

    def save_ohlcv_data(self, data: Union[OHLCV, List[OHLCV]]):
        """Save OHLCV data to a file.

        Args:
            data: OHLCV data to save
        """
        if self.ohlcv_file is None:
            raise ValueError("OHLCV file not initialized")
            
        if isinstance(data, OHLCV):
            self.ohlcv_file.write(data)
        else:
            for candle in data:
                self.ohlcv_file.write(candle)

    @abstractmethod
    def download_ohlcv(self, time_from: datetime, time_to: datetime,
                       on_progress: Optional[Callable[[datetime], None]] = None):
        """Download OHLCV data.

        In the implementation, call `self.save_ohlcv_data()` to save the data.

        Args:
            time_from: The start time
            time_to: The end time
            on_progress: Optional callback to call on progress
        """
        pass

    def load_ohlcv_data(self) -> OHLCVReader:
        """Load OHLCV data from the file.

        Returns:
            OHLCV reader
        """
        if self.ohlcv_path is None:
            raise ValueError("OHLCV path not initialized")
        return OHLCVReader(str(self.ohlcv_path))