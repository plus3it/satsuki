"""Setup for pytest."""


def pytest_addoption(parser):
    """Add command line options to pytest."""
    parser.addoption("--token", action="store", default=None)


def pytest_generate_tests(metafunc):
    """Parametrize tests with command line options."""
    option_value = metafunc.config.option.token
    if "token" in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("token", [option_value])
