"""Main CLI entry point for pynecore-data-provider."""

import typer
from rich.console import Console

from .commands.data import app as data_app

# Create main app
app = typer.Typer(
    help="PyneCore Data Provider - Download OHLCV data from various providers",
    add_completion=False,
)

# Add subcommands
app.add_typer(data_app, name="data", help="Download OHLCV data")

# Console for rich output
console = Console()


@app.callback()
def callback():
    """PyneCore Data Provider - Download OHLCV data from various providers."""
    pass


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()