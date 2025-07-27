"""Test importing the package."""

import unittest


class TestImport(unittest.TestCase):
    """Test importing the package."""

    def test_import_package(self):
        """Test importing the package."""
        try:
            import pynecore_data_provider
            self.assertTrue(True)
        except ImportError:
            self.fail("Failed to import pynecore_data_provider")

    def test_import_providers(self):
        """Test importing providers."""
        try:
            from pynecore_data_provider.providers import Provider
            self.assertTrue(True)
        except ImportError:
            self.fail("Failed to import Provider")

    def test_import_cli(self):
        """Test importing CLI."""
        try:
            from pynecore_data_provider.cli.main import app
            self.assertTrue(True)
        except ImportError:
            self.fail("Failed to import CLI")


if __name__ == "__main__":
    unittest.main()