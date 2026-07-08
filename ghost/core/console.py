"""
MIT License

Copyright (c) 2020-2024 EntySec

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Any, Dict

from badges.cmd import Cmd

from ghost import __version__
from ghost.core.device import Device


class Console(Cmd):
    """ Subclass of ghost.core module.

    This subclass of ghost.core modules is intended for providing
    main Ghost Framework console interface.
    """

    def __init__(self) -> None:
        super().__init__(
            prompt='(%lineghost%end)> ',
            intro="""%clear%end
   .--. .-.               .-.
  : .--': :              .' `.
  : : _ : `-.  .--.  .--.`. .'
  : :; :: .. :' .; :`._-.': :
  `.__.':_;:_;`.__.'`.__.':_;

--=[ %bold%whiteGhost Framework """ + __version__ + """%end
--=[ Developed by EntySec (%linehttps://entysec.com/%end)
"""
        )

        self.devices: Dict[int, Dict[str, Any]] = {}
        self._next_id = 0

    def do_exit(self, _) -> None:
        """ Exit Ghost Framework.

        :return None: None
        :raises EOFError: EOF error
        """

        for device in list(self.devices):
            self.devices[device]['device'].disconnect()
            del self.devices[device]

        raise EOFError

    def do_connect(self, args: list) -> None:
        """ Connect device.

        :param list args: arguments
        :return None: None
        """

        if len(args) < 2:
            self.print_usage("connect <host>:[port]")
            return

        address = args[1].split(':')

        if len(address) < 2:
            host, port = address[0], 5555
        else:
            try:
                host, port = address[0], int(address[1])
            except ValueError:
                self.print_error("Invalid port!")
                return

        device = Device(host=host, port=port)

        if device.connect():
            device_id = self._next_id
            self._next_id += 1

            self.devices.update({
                device_id: {
                    'host': host,
                    'port': str(port),
                    'device': device
                }
            })
            self.print_empty("")

            self.print_information(
                "Type %greendevices%end to list all connected devices.")
            self.print_information(
                f"Type %greeninteract {str(device_id)}%end "
                "to interact this device."
            )

    def do_devices(self, _) -> None:
        """ Show connected devices.

        :return None: None
        """

        if not self.devices:
            self.print_warning("No devices connected.")
            return

        devices = []

        for device in self.devices:
            devices.append(
                (device, self.devices[device]['host'],
                 self.devices[device]['port']))

        self.print_table("Connected Devices", ('ID', 'Host', 'Port'), *devices)

    def do_disconnect(self, args: list) -> None:
        """ Disconnect device.

        :param list args: arguments
        :return None: None
        """

        if len(args) < 2:
            self.print_usage("disconnect <id>")
            return

        try:
            device_id = int(args[1])
        except ValueError:
            self.print_error("Invalid device ID!")
            return

        if device_id not in self.devices:
            self.print_error("Invalid device ID!")
            return

        self.devices[device_id]['device'].disconnect()
        self.devices.pop(device_id)

    def do_interact(self, args: list) -> None:
        """ Interact with device.

        :param list args: arguments
        :return None: None
        """

        if len(args) < 2:
            self.print_usage("interact <id>")
            return

        try:
            device_id = int(args[1])
        except ValueError:
            self.print_error("Invalid device ID!")
            return

        if device_id not in self.devices:
            self.print_error("Invalid device ID!")
            return

        self.print_process(f"Interacting with device {str(device_id)}...")
        self.devices[device_id]['device'].interact()

    def shell(self) -> None:
        """ Run console shell.

        :return None: None
        """

        self.loop()
