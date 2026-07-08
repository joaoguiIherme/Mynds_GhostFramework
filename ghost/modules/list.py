"""
This module requires Ghost: https://github.com/EntySec/Ghost
Current source: https://github.com/EntySec/Ghost
"""

import datetime

from badges.cmd import Command


class ExternalCommand(Command):
    def __init__(self):
        super().__init__({
            'Category': "manage",
            'Name': "list",
            'Authors': [
                'Ivan Nikolskiy (enty8080) - module developer'
            ],
            'Description': "List directory contents.",
            'Usage': "list <remote_path>",
            'MinArgs': 1,
            'NeedsRoot': False
        })

    def run(self, args):
        """ List the contents of a remote directory in a table. """

        output = self.device.list(args[1])

        if output:
            headers = ('Name', 'Mode', 'Size', 'Modification Time')
            data = list()

            for entry in sorted(output):
                try:
                    timestamp = str(datetime.datetime.fromtimestamp(entry[3]))
                except (TypeError, ValueError, OSError, OverflowError):
                    timestamp = '-'
                data.append((entry[0].decode(), str(entry[1]), str(entry[2]), timestamp))

            self.print_table(f"Directory {args[1]}", headers, *data)
