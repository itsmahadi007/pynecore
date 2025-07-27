"""Data providers for PyneCore.

This package contains data providers for PyneCore.
"""

from pathlib import Path
from typing import List, Type

from .provider import Provider

# Import providers if available
try:
    from .ccxt import CCXTProvider
except ImportError:
    pass

try:
    from .capitalcom import CapitalComProvider
except ImportError:
    pass

# List of available providers
available_providers = tuple(
    p.stem for p in Path(__file__).parent.resolve().glob('*.py') if
    p.name not in ('__init__.py', 'provider.py')
)


def get_available_providers() -> List[Type[Provider]]:
    """Get list of available provider classes.

    Returns:
        List of provider classes
    """
    from ..utils import discover_providers
    return discover_providers()