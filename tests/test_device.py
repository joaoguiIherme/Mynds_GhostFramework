"""Unit tests for ghost.core.device.Device."""

import os
import stat

import pytest


# --- send_command --------------------------------------------------------

def test_send_command_returns_output(device):
    device.device.shell.return_value = "uid=0(root)"

    assert device.send_command("id") == "uid=0(root)"
    device.device.shell.assert_called_once_with("id")


def test_send_command_socket_error_returns_none(device):
    device.device.shell.side_effect = RuntimeError("boom")

    assert device.send_command("id") is None
    device.print_error.assert_called_once()


def test_send_command_output_false_returns_empty_string(device):
    device.device.shell.return_value = "ignored"

    assert device.send_command("id", output=False) == ""


# --- list ----------------------------------------------------------------

def test_list_returns_entries(device):
    device.device.list.return_value = ["a", "b"]

    assert device.list("/sdcard") == ["a", "b"]


def test_list_failure_returns_empty_and_reports(device):
    device.device.list.side_effect = OSError("nope")

    assert device.list("/sdcard") == []
    device.print_error.assert_called_once()


# --- upload (regression for the check_file contract bug) -----------------

def test_upload_missing_local_file_returns_false(device):
    # No monkeypatching: the real FS.check_file must raise RuntimeError for a
    # missing file, which upload() must translate into a clean False.
    result = device.upload("/definitely/not/here.bin", "/sdcard/")

    assert result is False
    device.print_error.assert_called_once()
    device.device.push.assert_not_called()


def test_upload_success(device, monkeypatch):
    monkeypatch.setattr(device, "check_file", lambda path: None)

    assert device.upload("/tmp/local.bin", "/sdcard/out.bin") is True
    device.device.push.assert_called_once_with("/tmp/local.bin", "/sdcard/out.bin")
    device.print_success.assert_called()


def test_upload_retries_with_appended_filename_when_target_is_dir(device, monkeypatch):
    monkeypatch.setattr(device, "check_file", lambda path: None)
    # First push (raw target) fails, retry (dir + filename) succeeds.
    device.device.push.side_effect = [RuntimeError("is a dir"), None]

    assert device.upload("/tmp/local.bin", "/sdcard") is True
    assert device.device.push.call_count == 2
    # Second call appends the basename to the directory path.
    assert device.device.push.call_args_list[1].args == ("/tmp/local.bin", "/sdcard/local.bin")


def test_upload_both_pushes_fail_returns_false(device, monkeypatch):
    monkeypatch.setattr(device, "check_file", lambda path: None)
    device.device.push.side_effect = RuntimeError("no such remote dir")

    assert device.upload("/tmp/local.bin", "/sdcard/missing") is False
    device.print_error.assert_called_once()


# --- download ------------------------------------------------------------

def test_download_success(device, monkeypatch):
    monkeypatch.setattr(device, "exists", lambda path: (True, False))

    assert device.download("/sdcard/f.txt", "/tmp/f.txt") is True
    device.device.pull.assert_called_once_with("/sdcard/f.txt", "/tmp/f.txt")


def test_download_to_directory_appends_basename(device, monkeypatch):
    monkeypatch.setattr(device, "exists", lambda path: (True, True))

    assert device.download("/sdcard/report.pdf", "/tmp/dir") is True
    device.device.pull.assert_called_once_with("/sdcard/report.pdf", "/tmp/dir/report.pdf")


def test_download_missing_target_returns_false(device, monkeypatch):
    monkeypatch.setattr(device, "exists", lambda path: (False, False))

    assert device.download("/sdcard/f.txt", "/tmp/gone") is False
    device.device.pull.assert_not_called()


# --- connect / disconnect ------------------------------------------------

def test_connect_success(device, monkeypatch):
    monkeypatch.setattr("ghost.core.device.PythonRSASigner", lambda *a, **k: object())
    monkeypatch.setattr(device, "get_keys", lambda: ("pub", "priv"))
    device.device.connect.return_value = True

    assert device.connect() is True
    device.print_success.assert_called_once()


def test_connect_failure_returns_false_with_context(device, monkeypatch):
    monkeypatch.setattr("ghost.core.device.PythonRSASigner", lambda *a, **k: object())
    monkeypatch.setattr(device, "get_keys", lambda: ("pub", "priv"))
    device.device.connect.side_effect = RuntimeError("auth failed")

    assert device.connect() is False
    device.print_error.assert_called_once()


def test_disconnect_closes_transport(device):
    device.disconnect()

    device.device.close.assert_called_once()


# --- is_rooted -----------------------------------------------------------

def test_is_rooted_true_when_su_present(device):
    device.device.shell.return_value = "/system/bin/su"

    assert device.is_rooted() is True


@pytest.mark.parametrize("shell_output", ["", "   ", None])
def test_is_rooted_false_when_no_su(device, shell_output):
    device.device.shell.return_value = shell_output

    assert device.is_rooted() is False


# --- get_keys / key hardening -------------------------------------------

def test_get_keys_generates_key_with_secure_permissions(tmp_path):
    from ghost.core.device import Device

    key_path = tmp_path / "subdir" / "key"
    dev = Device(host="127.0.0.1", port=5555, key_filename=str(key_path))

    pub, priv = dev.get_keys()

    assert priv and pub
    assert key_path.exists()
    # Private key must be owner read/write only (0600).
    mode = stat.S_IMODE(os.stat(key_path).st_mode)
    assert mode == 0o600, f"expected 0600, got {oct(mode)}"
    # Parent directory created with restricted permissions.
    dir_mode = stat.S_IMODE(os.stat(key_path.parent).st_mode)
    assert dir_mode == 0o700, f"expected 0700, got {oct(dir_mode)}"


def test_default_key_path_is_under_home(monkeypatch, tmp_path):
    from ghost.core.device import Device

    monkeypatch.setenv("HOME", str(tmp_path))
    dev = Device(host="127.0.0.1", port=5555)

    assert dev.key_file == os.path.join(str(tmp_path), ".ghost", "key")
