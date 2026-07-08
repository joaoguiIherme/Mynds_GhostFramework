"""
This module requires Ghost: https://github.com/EntySec/Ghost
Current source: https://github.com/EntySec/Ghost
"""

import shlex
import sys
import termios
import tty

from badges.cmd import Command


class ExternalCommand(Command):
    def __init__(self):
        super().__init__({
            'Category': "manage",
            'Name': "keyboard",
            'Authors': [
                'Ivan Nikolskiy (enty8080) - module developer'
            ],
            'Description': "Interact with device keyboard.",
            'Usage': "keyboard",
            'MinArgs': 0,
            'NeedsRoot': False
        })

    @staticmethod
    def get_char():
        """ Read a single character from stdin in raw mode. """

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def run(self, _):
        """ Forward keyboard input to the device as `input text` events. """

        self.print_process("Interacting with keyboard...")
        self.print_success("Interactive connection spawned!")

        self.print_information("Type text below.")
        while True:
            self.device.send_command(f"input text {shlex.quote(self.get_char())}")
