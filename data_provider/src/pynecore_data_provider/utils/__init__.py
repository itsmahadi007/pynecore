"""Utility functions for pynecore-data-provider."""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import List, Type, Dict, Any

from ..providers import Provider


def discover_providers() -> List[Type[Provider]]:
    """Discover all available provider classes.

    Returns:
        List of provider classes
    """
    from .. import providers as providers_module
    
    result = []
    
    # Get the package path
    package_path = Path(providers_module.__file__).parent
    
    # Iterate through all modules in the package
    for _, name, _ in pkgutil.iter_modules([str(package_path)]):
        # Skip __init__.py and provider.py
        if name in ['__init__', 'provider']:
            continue
            
        # Import the module
        module = importlib.import_module(f"{providers_module.__name__}.{name}")
        
        # Find all classes that inherit from Provider
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Provider) and obj != Provider:
                result.append(obj)
    
    return result


def load_provider_class(provider_name: str) -> Type[Provider]:
    """Load a provider class by name.

    Args:
        provider_name: Name of the provider class

    Returns:
        Provider class

    Raises:
        ImportError: If provider class cannot be found
    """
    from .. import providers as providers_module
    
    # Try to get the provider class directly
    try:
        return getattr(providers_module, provider_name)
    except AttributeError:
        pass
    
    # Try to find the provider class in submodules
    for provider_class in discover_providers():
        if provider_class.__name__ == provider_name:
            return provider_class
    
    raise ImportError(f"Provider '{provider_name}' not found")