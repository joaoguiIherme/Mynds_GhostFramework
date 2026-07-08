"""Unit tests for the ghost.modules command plugins."""

import shlex
from types import SimpleNamespace

import pytest

from ghost.modules.activity import ExternalCommand as ActivityCommand
from ghost.modules.battery import ExternalCommand as BatteryCommand
from ghost.modules.download import ExternalCommand as DownloadCommand
from ghost.modules.keyboard import ExternalCommand as KeyboardCommand
from ghost.modules.list import ExternalCommand as ListCommand
from ghost.modules.network import ExternalCommand as NetworkCommand
from ghost.modules.openurl import ExternalCommand as OpenurlCommand
from ghost.modules.press import ExternalCommand as PressCommand
from ghost.modules.screenshot import ExternalCommand as ScreenshotCommand
from ghost.modules.shell import ExternalCommand as ShellCommand
from ghost.modules.sleep import ExternalCommand as SleepCommand
from ghost.modules.upload import ExternalCommand as UploadCommand
from ghost.modules.wifi import ExternalCommand as WifiCommand


def _last_command(cmd):
    """Return the command string of the most recent send_command call."""

    return cmd.device.send_command.call_args.args[0]


# --- openurl (CRITICAL injection regression) -----------------------------

def test_openurl_prepends_scheme(make_module):
    cmd = make_module(OpenurlCommand)

    cmd.run(["openurl", "example.com"])

    assert _last_command(cmd) == \
        f"am start -a android.intent.action.VIEW -d {shlex.quote('http://example.com')}"


def test_openurl_keeps_https(make_module):
    cmd = make_module(OpenurlCommand)

    cmd.run(["openurl", "https://example.com"])

    assert shlex.quote("https://example.com") in _last_command(cmd)


def test_openurl_neutralizes_injection(make_module):
    cmd = make_module(OpenurlCommand)
    payload = 'http://x"; reboot; #'

    cmd.run(["openurl", payload])

    sent = _last_command(cmd)
    # The whole payload is a single shell-quoted token -> no bare metacharacters.
    assert sent == f"am start -a android.intent.action.VIEW -d {shlex.quote(payload)}"


def test_openurl_does_not_mutate_args(make_module):
    cmd = make_module(OpenurlCommand)
    args = ["openurl", "example.com"]

    cmd.run(args)

    assert args[1] == "example.com"


# --- keyboard (HIGH injection pattern) -----------------------------------

def test_keyboard_quotes_each_char(make_module, monkeypatch):
    cmd = make_module(KeyboardCommand)
    monkeypatch.setattr(cmd, "get_char", lambda: ";reboot")
    # Break the infinite loop after the first iteration.
    cmd.device.send_command.side_effect = [None, KeyboardInterrupt]

    with pytest.raises(KeyboardInterrupt):
        cmd.run(None)

    first = cmd.device.send_command.call_args_list[0].args[0]
    assert first == f"input text {shlex.quote(';reboot')}"


# --- press (HIGH validation) ---------------------------------------------

def test_press_valid_keycode(make_module):
    cmd = make_module(PressCommand)

    cmd.run(["press", "3"])

    assert _last_command(cmd) == "input keyevent 3"


@pytest.mark.parametrize("bad", ["124", "999", "abc", "-1", "3.5"])
def test_press_rejects_invalid_keycode(make_module, bad):
    cmd = make_module(PressCommand)

    cmd.run(["press", bad])

    cmd.print_error.assert_called_once()
    cmd.device.send_command.assert_not_called()


# --- wifi ----------------------------------------------------------------

def test_wifi_on(make_module):
    cmd = make_module(WifiCommand)

    cmd.run(["wifi", "on"])

    assert _last_command(cmd) == "svc wifi enable"


def test_wifi_off(make_module):
    cmd = make_module(WifiCommand)

    cmd.run(["wifi", "off"])

    assert _last_command(cmd) == "svc wifi disable"


def test_wifi_invalid_shows_usage(make_module):
    cmd = make_module(WifiCommand)

    cmd.run(["wifi", "maybe"])

    cmd.print_usage.assert_called_once()
    cmd.device.send_command.assert_not_called()


# --- shell ---------------------------------------------------------------

def test_shell_joins_arguments(make_module):
    cmd = make_module(ShellCommand)
    cmd.device.send_command.return_value = "ok"

    cmd.run(["shell", "ls", "-la", "/sdcard"])

    assert _last_command(cmd) == "ls -la /sdcard"
    cmd.print_empty.assert_called_once_with("ok")


def test_shell_guards_none_output(make_module):
    cmd = make_module(ShellCommand)
    cmd.device.send_command.return_value = None

    cmd.run(["shell", "id"])

    cmd.print_empty.assert_called_once_with("")


# --- activity / battery --------------------------------------------------

@pytest.mark.parametrize("command_cls,expected", [
    (ActivityCommand, "dumpsys activity"),
    (BatteryCommand, "dumpsys battery"),
])
def test_info_modules_send_and_print(make_module, command_cls, expected):
    cmd = make_module(command_cls)
    cmd.device.send_command.return_value = "info"

    cmd.run(None)

    assert _last_command(cmd) == expected
    cmd.print_empty.assert_called_once_with("info")


@pytest.mark.parametrize("command_cls", [ActivityCommand, BatteryCommand])
def test_info_modules_guard_none_output(make_module, command_cls):
    cmd = make_module(command_cls)
    cmd.device.send_command.return_value = None

    cmd.run(None)

    cmd.print_empty.assert_called_once_with("")


# --- sleep ---------------------------------------------------------------

def test_sleep_sends_power_keyevent(make_module):
    cmd = make_module(SleepCommand)

    cmd.run(None)

    assert _last_command(cmd) == "input keyevent 26"


# --- list ----------------------------------------------------------------

def test_list_renders_table(make_module):
    cmd = make_module(ListCommand)
    cmd.device.list.return_value = [(b"file.txt", 33188, 10, 1_600_000_000)]

    cmd.run(["list", "/sdcard"])

    cmd.print_table.assert_called_once()


def test_list_tolerates_bad_timestamp(make_module):
    cmd = make_module(ListCommand)
    cmd.device.list.return_value = [(b"weird", 33188, 0, None)]

    # Must not raise despite the None timestamp.
    cmd.run(["list", "/sdcard"])

    cmd.print_table.assert_called_once()
    # The rendered row falls back to a placeholder timestamp.
    rendered_rows = cmd.print_table.call_args.args[2:]
    assert rendered_rows[0][3] == "-"


def test_list_empty_directory_prints_nothing(make_module):
    cmd = make_module(ListCommand)
    cmd.device.list.return_value = []

    cmd.run(["list", "/sdcard"])

    cmd.print_table.assert_not_called()


# --- network (HIGH None-join regression) ---------------------------------

def _net_args(**flags):
    defaults = dict(arp=False, ipconfig=False, iproute=False, locate=False,
                    stats=False, ports=False, forwarding=False, services=False)
    defaults.update(flags)
    return SimpleNamespace(**defaults)


@pytest.mark.parametrize("flag,expected", [
    ("arp", "cat /proc/net/arp"),
    ("ipconfig", "ip addr show"),
    ("iproute", "ip route show"),
    ("locate", "dumpsys location"),
    ("stats", "cat /proc/net/netstat"),
    ("ports", "busybox netstat -an"),
    ("services", "service list"),
    ("forwarding", "cat /proc/sys/net/ipv4/ip_forward"),
])
def test_network_each_flag_sends_expected_command(make_module, flag, expected):
    cmd = make_module(NetworkCommand)
    cmd.device.send_command.return_value = "out"

    cmd.run(_net_args(**{flag: True}))

    cmd.device.send_command.assert_called_once_with(expected)
    cmd.print_empty.assert_called_once_with("out")


def test_network_filters_none_before_join(make_module):
    cmd = make_module(NetworkCommand)
    # arp succeeds, ipconfig returns None (socket dropped) -> must not crash.
    cmd.device.send_command.side_effect = ["arp-out", None]

    cmd.run(_net_args(arp=True, ipconfig=True))

    cmd.print_empty.assert_called_once_with("arp-out")


# --- screenshot ----------------------------------------------------------

def test_screenshot_uses_unique_remote_path_and_downloads(make_module):
    cmd = make_module(ScreenshotCommand)

    cmd.run(["screenshot", "/tmp/shot.png"])

    calls = [c.args[0] for c in cmd.device.send_command.call_args_list]
    screencap_cmd, rm_cmd = calls[0], calls[1]
    remote = screencap_cmd.split(" ", 1)[1]

    assert remote.startswith("/data/local/tmp/screenshot_")
    assert rm_cmd == f"rm {remote}"
    cmd.device.download.assert_called_once_with(remote, "/tmp/shot.png")


def test_screenshot_paths_differ_between_runs(make_module):
    cmd = make_module(ScreenshotCommand)

    cmd.run(["screenshot", "/tmp/a.png"])
    cmd.run(["screenshot", "/tmp/b.png"])

    remotes = [c.args[0] for c in cmd.device.download.call_args_list]
    assert remotes[0] != remotes[1]


# --- upload / download delegation ----------------------------------------

def test_upload_module_delegates(make_module):
    cmd = make_module(UploadCommand)

    cmd.run(["upload", "/tmp/l.bin", "/sdcard/r.bin"])

    cmd.device.upload.assert_called_once_with("/tmp/l.bin", "/sdcard/r.bin")


def test_download_module_delegates(make_module):
    cmd = make_module(DownloadCommand)

    cmd.run(["download", "/sdcard/r.bin", "/tmp/l.bin"])

    cmd.device.download.assert_called_once_with("/sdcard/r.bin", "/tmp/l.bin")
