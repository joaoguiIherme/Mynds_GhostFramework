"""
This module requires Ghost: https://github.com/EntySec/Ghost
Current source: https://github.com/EntySec/Ghost
"""

import shlex

from badges.cmd import Command


class ExternalCommand(Command):
    def __init__(self):
        super().__init__({
            'Category': "manage",
            'Name': "openurl",
            'Authors': [
                'Ivan Nikolskiy (enty8080) - module developer'
            ],
            'Description': "Open URL on device.",
            'Usage': "openurl <url>",
            'MinArgs': 1,
            'NeedsRoot': False
        })

    def run(self, args):
        """ Open the given URL on the device via an ACTION_VIEW intent. """

        url = args[1] if args[1].startswith(("http://", "https://")) \
            else "http://" + args[1]

        self.device.send_command(
            f"am start -a android.intent.action.VIEW -d {shlex.quote(url)}")
