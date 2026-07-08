"""
This module requires Ghost: https://github.com/EntySec/Ghost
Current source: https://github.com/EntySec/Ghost
"""

import uuid

from badges.cmd import Command


class ExternalCommand(Command):
    def __init__(self):
        super().__init__({
            'Category': "manage",
            'Name': "screenshot",
            'Authors': [
                'Ivan Nikolskiy (enty8080) - module developer'
            ],
            'Description': "Take device screenshot.",
            'Usage': "screenshot <local_path>",
            'MinArgs': 1,
            'NeedsRoot': False
        })

    def run(self, args):
        """ Capture a device screenshot and download it to a local path. """

        remote_path = f"/data/local/tmp/screenshot_{uuid.uuid4().hex}.png"

        self.print_process("Taking screenshot...")
        self.device.send_command(f"screencap {remote_path}")

        self.device.download(remote_path, args[1])
        self.device.send_command(f"rm {remote_path}")
