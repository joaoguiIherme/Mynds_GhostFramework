"""Shared pytest fixtures and helpers for the Ghost Framework test suite.

The modules and core classes inherit their ``print_*`` UI helpers and
``device`` wiring from the ``badges`` framework. For unit tests we replace
those with mocks so we can assert behaviour without a real ADB connection or
terminal output.
"""

from unittest.mock import MagicMock

import pytest

# Names of the badges print helpers the code under test relies on.
PRINT_METHODS = (
    "print_empty",
    "print_error",
    "print_process",
    "print_success",
    "print_information",
    "print_usage",
    "print_warning",
    "print_table",
)


def mock_prints(obj):
    """Replace every badges ``print_*`` helper on ``obj`` with a MagicMock."""

    for name in PRINT_METHODS:
        setattr(obj, name, MagicMock(name=name))
    return obj


@pytest.fixture
def make_module():
    """Factory: build a module command with a mocked device and prints.

    Returns a callable ``build(ExternalCommand, device=None)`` yielding the
    instantiated command whose ``device`` attribute and ``print_*`` helpers are
    mocks ready for assertions.
    """

    def build(command_cls, device=None):
        cmd = command_cls()
        cmd.device = device if device is not None else MagicMock(name="device")
        mock_prints(cmd)
        return cmd

    return build


@pytest.fixture
def device():
    """A real ``Device`` instance with its ADB transport and prints mocked.

    No network is touched: ``self.device`` (the ``AdbDeviceTcp`` transport) is
    swapped for a MagicMock.
    """

    from ghost.core.device import Device

    dev = Device(host="127.0.0.1", port=5555)
    dev.device = MagicMock(name="adb_transport")
    mock_prints(dev)
    return dev
