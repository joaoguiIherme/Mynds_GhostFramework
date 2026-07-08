"""End-to-end integration tests for the interactive loops.

These drive the *real* code paths that the mocked unit tests cannot reach:
the console REPL (``Console.shell`` -> ``badges`` ``loop``) and the raw-tty
``keyboard.get_char`` reader. They run the actual program inside a pseudo
terminal via ``pexpect``, so they exercise prompt handling, command dispatch,
and terminal I/O exactly as a user would.

No Android device is involved -- only device-independent commands (help,
devices, unknown input, invalid connect) and the standalone char reader.
"""

import os
import sys

import pytest

pexpect = pytest.importorskip("pexpect")

# PTYs are POSIX-only; skip the whole module elsewhere.
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.name != "posix", reason="pexpect PTY tests require POSIX"),
]

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPAWN_TIMEOUT = 20


def _spawn(args):
    """Spawn a Python child in a PTY rooted at the project directory."""

    return pexpect.spawn(
        sys.executable,
        args,
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT},
        encoding="utf-8",
        timeout=SPAWN_TIMEOUT,
        dimensions=(40, 120),
    )


# --- console REPL loop ---------------------------------------------------

def test_console_session_help_devices_exit():
    """A full interactive session: banner -> help -> devices -> exit."""

    child = _spawn(["-m", "ghost"])
    try:
        child.expect("Ghost Framework")

        child.sendline("help")
        child.expect("Core Commands")
        child.expect("interact")  # command listed in the help table

        child.sendline("devices")
        child.expect("No devices connected")

        child.sendline("exit")
        child.expect(pexpect.EOF)
    finally:
        child.close(force=True)


def test_console_reports_unknown_command():
    child = _spawn(["-m", "ghost"])
    try:
        child.expect("Ghost Framework")

        child.sendline("notacommand")
        child.expect("Unrecognized command")

        child.sendline("exit")
        child.expect(pexpect.EOF)
    finally:
        child.close(force=True)


def test_console_rejects_invalid_port_over_repl():
    """The ValueError guard in do_connect must surface through the live loop."""

    child = _spawn(["-m", "ghost"])
    try:
        child.expect("Ghost Framework")

        child.sendline("connect 10.0.0.1:notaport")
        child.expect("Invalid port")

        child.sendline("exit")
        child.expect(pexpect.EOF)
    finally:
        child.close(force=True)


# --- keyboard raw-tty reader ---------------------------------------------

# Child prints READY only after import, then blocks in get_char(). The ready
# handshake matters: tty.setraw() flushes pending input (TCSAFLUSH), so the
# byte must be sent *after* raw mode is entered, not before.
_GETCHAR_CHILD = (
    "import sys;"
    "from ghost.modules.keyboard import ExternalCommand;"
    "sys.stdout.write('READY\\n');sys.stdout.flush();"
    "ch=ExternalCommand().get_char();"
    "sys.stdout.write('GOTCHAR='+repr(ch)+'\\n');sys.stdout.flush()"
)


@pytest.mark.parametrize("char", ["Z", "a", "7"])
def test_get_char_reads_single_byte_from_tty(char):
    child = _spawn(["-c", _GETCHAR_CHILD])
    try:
        child.expect("READY")
        child.send(char)
        child.expect(r"GOTCHAR='%s'" % char)
        child.expect(pexpect.EOF)
    finally:
        child.close(force=True)
