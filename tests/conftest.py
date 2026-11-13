def pytest_configure(config):
    """Register the markers here, as cibuildwheel runs the tests without pyproject.toml."""
    config.addinivalue_line("markers", "numcodecs: tests of the numcodecs codec")
    config.addinivalue_line("markers", "zarr: tests of zarr integration")
