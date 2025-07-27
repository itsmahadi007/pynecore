"""Data download commands for pynecore-data-provider.

This module provides commands for downloading OHLCV data from various providers.
"""

import enum
import importlib
import os
import sys
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Optional, List, Callable, Any, Dict, Type

import typer
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn

from pynecore.core.ohlcv_file import OHLCVReader
from pynecore.core.syminfo import SymInfo

from ...providers import get_available_providers, Provider

# Create Typer app
app = typer.Typer(help="Download OHLCV data from various providers")

# Console for rich output
console = Console()


class AvailableProvidersEnum(str, enum.Enum):
    """Enum of available providers."""
    # This will be populated dynamically
    pass


class TimeframeEnum(str, enum.Enum):
    """Enum of available timeframes."""
    M1 = "1"
    M5 = "5"
    M10 = "10"
    M15 = "15"
    M30 = "30"
    H1 = "60"
    H2 = "120"
    H4 = "240"
    D1 = "1D"
    W1 = "1W"
    MN1 = "1M"


def parse_date_or_days(value: str) -> datetime:
    """Parse a date string or days ago.

    Args:
        value: Date string in YYYY-MM-DD format or number of days ago

    Returns:
        Parsed datetime
    """
    if value.isdigit():
        # Parse as days ago
        days_ago = int(value)
        return datetime.now(UTC) - timedelta(days=days_ago)
    else:
        # Parse as date string
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise typer.BadParameter(f"Invalid date format: {value}. Use YYYY-MM-DD or number of days ago.")


# Dynamically create the AvailableProvidersEnum
def _create_providers_enum() -> Type[enum.Enum]:
    """Create the AvailableProvidersEnum dynamically based on available providers."""
    providers = get_available_providers()
    enum_dict = {p.__name__: p.__name__ for p in providers}
    
    if not enum_dict:
        # Add a placeholder if no providers are available
        enum_dict = {"NoProvidersAvailable": "NoProvidersAvailable"}
    
    return enum.Enum('AvailableProvidersEnum', enum_dict)


# Replace the placeholder enum with the dynamically created one
AvailableProvidersEnum = _create_providers_enum()


@app.command()
def download(
    provider: AvailableProvidersEnum = typer.Argument(..., help="Provider to use for downloading data"),
    symbol: str = typer.Argument(..., help="Symbol to download data for"),
    timeframe: TimeframeEnum = typer.Option(TimeframeEnum.D1, help="Timeframe to download data for"),
    time_from: str = typer.Option("30", "--from", help="Start date (YYYY-MM-DD) or days ago"),
    time_to: str = typer.Option("0", "--to", help="End date (YYYY-MM-DD) or days ago"),
    list_symbols: bool = typer.Option(False, "--list-symbols", help="List available symbols and exit"),
    show_info: bool = typer.Option(False, "--show-info", help="Show symbol information and exit"),
    truncate: bool = typer.Option(False, "--truncate", help="Truncate existing OHLCV file"),
    ohlcv_dir: Optional[Path] = typer.Option(None, help="Directory to save OHLCV data"),
    config_dir: Optional[Path] = typer.Option(None, help="Directory with providers.toml config"),
):
    """Download OHLCV data from various providers."""
    # Get the provider class
    provider_name = provider.value
    provider_module = importlib.import_module("...", __name__).providers
    provider_class = getattr(provider_module, provider_name)

    # Handle list_symbols flag
    if list_symbols:
        console.print(f"[bold]Listing symbols for {provider_name}...[/bold]")
        try:
            provider_instance = provider_class(config_dir=config_dir)
            symbols = provider_instance.get_list_of_symbols()
            for sym in symbols:
                console.print(sym)
            return
        except Exception as e:
            console.print(f"[bold red]Error listing symbols: {str(e)}[/bold red]")
            sys.exit(1)

    # Create provider instance
    try:
        provider_instance = provider_class(
            symbol=symbol,
            timeframe=timeframe.value,
            ohlcv_dir=ohlcv_dir,
            config_dir=config_dir
        )
    except Exception as e:
        console.print(f"[bold red]Error creating provider: {str(e)}[/bold red]")
        sys.exit(1)

    # Handle show_info flag
    if show_info:
        console.print(f"[bold]Getting symbol info for {symbol}...[/bold]")
        try:
            sym_info = provider_instance.get_symbol_info()
            if sym_info is None:
                sym_info = provider_instance.update_symbol_info()
                provider_instance.save_symbol_info(sym_info)
            
            console.print(f"[bold]Symbol Information for {symbol}:[/bold]")
            for key, value in sym_info._asdict().items():
                console.print(f"  {key}: {value}")
            return
        except Exception as e:
            console.print(f"[bold red]Error getting symbol info: {str(e)}[/bold red]")
            sys.exit(1)

    # Parse dates
    from_date = parse_date_or_days(time_from)
    to_date = parse_date_or_days(time_to)

    # Check if we need to truncate
    ohlcv_path = provider_instance.get_ohlcv_path()
    if truncate and ohlcv_path.exists():
        console.print(f"[bold yellow]Truncating {ohlcv_path}[/bold yellow]")
        try:
            os.remove(ohlcv_path)
        except Exception as e:
            console.print(f"[bold red]Error truncating file: {str(e)}[/bold red]")
            sys.exit(1)

    # Check if we need to resume download
    last_timestamp = None
    if ohlcv_path.exists():
        try:
            reader = OHLCVReader(ohlcv_path)
            last_timestamp = reader.end_timestamp / 1000  # Convert from milliseconds
            if last_timestamp:
                last_date = datetime.fromtimestamp(last_timestamp, UTC)
                console.print(f"[bold green]Resuming download from {last_date}[/bold green]")
                from_date = last_date
        except Exception as e:
            console.print(f"[bold yellow]Warning: Could not read existing file: {str(e)}[/bold yellow]")

    # Get symbol info
    sym_info = provider_instance.get_symbol_info()
    if sym_info is None:
        console.print(f"[bold]Getting symbol info for {symbol}...[/bold]")
        try:
            sym_info = provider_instance.update_symbol_info()
            provider_instance.save_symbol_info(sym_info)
        except Exception as e:
            console.print(f"[bold red]Error getting symbol info: {str(e)}[/bold red]")
            sys.exit(1)

    # Download data
    console.print(f"[bold]Downloading {symbol} {timeframe.value} data from {from_date} to {to_date}...[/bold]")

    # Create progress bar
    with Progress(
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        BarColumn(),
        TextColumn("{task.fields[date]}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task_id = progress.add_task(
            f"Downloading {symbol}",
            total=(to_date - from_date).total_seconds(),
            date=from_date.strftime("%Y-%m-%d %H:%M:%S")
        )

        def cb_progress(current_date: datetime):
            progress.update(
                task_id,
                completed=(current_date - from_date).total_seconds(),
                date=current_date.strftime("%Y-%m-%d %H:%M:%S")
            )

        try:
            provider_instance.download_ohlcv(from_date, to_date, cb_progress)
        except Exception as e:
            console.print(f"[bold red]Error downloading data: {str(e)}[/bold red]")
            sys.exit(1)

    console.print(f"[bold green]Download complete! Data saved to {ohlcv_path}[/bold green]")