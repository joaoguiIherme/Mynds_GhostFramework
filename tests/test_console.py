"""Unit tests for ghost.core.console.Console."""

from unittest.mock import MagicMock

import pytest

from conftest import mock_prints


@pytest.fixture
def console(monkeypatch):
    """A Console with prints mocked and Device patched to never touch a network.

    ``ghost.core.console.Device`` is replaced by a factory returning a fresh
    MagicMock per connection whose ``connect()`` returns True.
    """

    from ghost.core.console import Console

    def fake_device(*args, **kwargs):
        dev = MagicMock(name="Device")
        dev.connect.return_value = True
        return dev

    monkeypatch.setattr("ghost.core.console.Device", fake_device)

    con = Console()
    mock_prints(con)
    return con


def test_connect_assigns_sequential_ids(console):
    console.do_connect(["connect", "10.0.0.1"])
    console.do_connect(["connect", "10.0.0.2"])

    assert sorted(console.devices) == [0, 1]


def test_connect_default_port_is_5555(console):
    console.do_connect(["connect", "10.0.0.1"])

    assert console.devices[0]["port"] == "5555"


def test_connect_parses_explicit_port(console):
    console.do_connect(["connect", "10.0.0.1:4444"])

    assert console.devices[0]["port"] == "4444"


def test_connect_invalid_port_reports_and_skips(console):
    console.do_connect(["connect", "10.0.0.1:notaport"])

    assert console.devices == {}
    console.print_error.assert_called_once()


def test_connect_requires_argument(console):
    console.do_connect(["connect"])

    assert console.devices == {}
    console.print_usage.assert_called_once()


def test_device_id_does_not_collide_after_disconnect(console):
    # Regression: IDs were derived from len(devices), so reconnecting after a
    # disconnect could overwrite an existing entry and leak its socket.
    console.do_connect(["connect", "10.0.0.1"])  # id 0
    console.do_connect(["connect", "10.0.0.2"])  # id 1
    console.do_connect(["connect", "10.0.0.3"])  # id 2

    console.do_disconnect(["disconnect", "1"])   # remove id 1
    console.do_connect(["connect", "10.0.0.4"])  # must be id 3, not 2

    assert sorted(console.devices) == [0, 2, 3]
    assert console.devices[2]["host"] == "10.0.0.3"  # untouched


def test_disconnect_calls_device_disconnect(console):
    console.do_connect(["connect", "10.0.0.1"])
    dev = console.devices[0]["device"]

    console.do_disconnect(["disconnect", "0"])

    dev.disconnect.assert_called_once()
    assert console.devices == {}


def test_disconnect_non_numeric_id_reports(console):
    console.do_disconnect(["disconnect", "abc"])

    console.print_error.assert_called_once()


def test_disconnect_unknown_id_reports(console):
    console.do_disconnect(["disconnect", "99"])

    console.print_error.assert_called_once()


def test_interact_non_numeric_id_reports(console):
    console.do_interact(["interact", "xyz"])

    console.print_error.assert_called_once()


def test_interact_unknown_id_reports(console):
    console.do_interact(["interact", "5"])

    console.print_error.assert_called_once()


def test_interact_dispatches_to_device(console):
    console.do_connect(["connect", "10.0.0.1"])
    dev = console.devices[0]["device"]

    console.do_interact(["interact", "0"])

    dev.interact.assert_called_once()


def test_devices_empty_warns(console):
    console.do_devices(None)

    console.print_warning.assert_called_once()
    console.print_table.assert_not_called()


def test_devices_lists_connected(console):
    console.do_connect(["connect", "10.0.0.1"])
    console.do_connect(["connect", "10.0.0.2"])

    console.do_devices(None)

    console.print_table.assert_called_once()


def test_exit_disconnects_all_devices(console):
    console.do_connect(["connect", "10.0.0.1"])
    dev = console.devices[0]["device"]

    with pytest.raises(EOFError):
        console.do_exit(None)

    dev.disconnect.assert_called_once()
    assert console.devices == {}
