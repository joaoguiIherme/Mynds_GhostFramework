"""
This module requires Ghost: https://github.com/EntySec/Ghost
Current source: https://github.com/EntySec/Ghost
"""

from badges.cmd import Command


class ExternalCommand(Command):
    def __init__(self):
        super().__init__({
            'Category': "manage",
            'Name': "press",
            'Authors': [
                'Ivan Nikolskiy (enty8080) - module developer'
            ],
            'Description': "Press device button by keycode.",
            'Usage': "press <keycode>",
            'MinArgs': 1,
            'NeedsRoot': False
        })

    def run(self, args):
        """ Send a key event to the device by numeric keycode (0-123). """

        max_keycode = 124

        if not args[1].isdigit() or int(args[1]) >= max_keycode:
            self.print_error("Invalid keycode!")
            return

        self.device.send_command(f"input keyevent {int(args[1])}")
