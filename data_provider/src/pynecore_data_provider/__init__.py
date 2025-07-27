"""PyneCore Data Provider Plugin

This package provides data provider plugins for PyneCore.
"""

__version__ = "0.1.0"

# Import key classes for easy access
from .providers import Provider, get_available_providers

# Import specific providers if available
try:
    from .providers import CCXTProvider
except ImportError:
    pass

try:
    from .providers import CapitalComProvider
except ImportError:
    pass

# Import utility functions
from .utils import discover_providers, load_provider_class

# Import core types
from .core import OHLCVWriter, OHLCVReader, SymInfo, SymInfoInterval, SymInfoSession
from .types import OHLCV

__all__ = [
    "Provider",
    "get_available_providers",
    "discover_providers", 
    "load_provider_class",
    "OHLCVWriter",
    "OHLCVReader",
    "SymInfo",
    "SymInfoInterval",
    "SymInfoSession",
    "OHLCV",
    # Conditional exports
    "CCXTProvider",  # Available if ccxt is installed
    "CapitalComProvider",  # Available if httpx is installed
]