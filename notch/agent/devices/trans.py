#!/usr/bin/env python
#
# Copyright 2009 Andrew Fort. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Abstract device transport."""


import re

import pexpect

import notch.agent.errors


STRIP_ANSI = [
    re.compile(r'\x1b(?:\[|\(?:|\))[;?0-9]*[0-9A-Za-z]'),
    re.compile(r'\x1b(?:\[|\(?:|\))[;?0-9]*[0-9A-Za-z]'),
    re.compile(r'[\x03|\x1a]'),
    ]


class Error(Exception):
    pass


class DeviceTransport(object):
    """Abstract device transport.

    Attributes:
      address: A string hostname or IPAddr object.
      port: An int, the TCP port to connect to. None uses the default port.
      timeouts: A device.Timeouts namedtuple, timeout values to use.
      strip_ansi: A boolean, if True, strip ANSI escape sequences.
    """

    DEFAULT_PORT = None
    DEFAULT_TIMEOUT_CONNECT = 30
    DEFAULT_TIMEOUT_RESP_SHORT = 7
    DEFAULT_TIMEOUT_RESP_LONG = 180
    DEFAULT_TIMEOUT_DISCONNECT = 15

    def __init__(self, address=None, port=None, timeouts=None, strip_ansi=None,
                 **kwargs):
        """Initializer.

        Args:
          address: A string hostname or IPAddr object.
          port: An int, the TCP port to connect to. None uses the default port.
          timeouts: A device.Timeouts namedtuple, timeout values to use.
          strip_ansi: A boolean, if True, strip ANSI escape sequences.
        """
        _ = kwargs
        self.address = address
        self.timeouts = timeouts
        self.port = port or self.DEFAULT_PORT
        self.strip_ansi = strip_ansi
        self._c = None

    def _strip_ansi(self, data):
        for reg in STRIP_ANSI:
            data = reg.sub('', data)
        return data
        
    @property
    def match(self):
        """Returns the most recent expect match."""
        raise NotImplementedError

    @property
    def before(self):
        """Returns the most recent data before the expect match."""
        raise NotImplementedError

    @property
    def after(self):
        """Returns the most recent data after the expect match."""
        raise NotImplementedError

    def connect(self, credential):
        """Connects to the device using a given credential."""
        raise NotImplementedError

    def flush(self):
        """Eagerly flush any remaining data from the read fd."""
        pass

    def disconnect(self):
        """Closes the telnet session and returns any remaining data."""
        raise NotImplementedError

    def write(self, s):
        """Writes data to the remote transport device."""
        raise NotImplementedError
        
    def expect(self, re_list, timeout=None):
        """Expects one of a list of regular expressions from the device."""
        raise NotImplementedError

    def command(self, command, prompt, timeout=None, expect_trailer='\r\n',
                command_trailer='\n', expect_command=True,
                pager=None, pager_response=' '):
        """Executes a command.

        This returns any data after the CLI command sent, prior to the
        CLI prompt after the output ceases.
        """
        timeout_long = timeout or self.timeouts.resp_long
        timeout_short = timeout or self.timeouts.resp_short

        # Find the prompt and flush the expect buffer.
        self.write(command_trailer)
        if isinstance(prompt, str):
            esc_prompt = re.escape(prompt)
        else:
            esc_prompt = prompt
        i = self.expect([esc_prompt, pexpect.EOF, pexpect.TIMEOUT],
                        timeout_short)
        if i == 1:
            exc = notch.agent.errors.CommandError(
                'EOF received during command %r' % command)
            exc.retry = True
            raise exc
        elif i == 2:
            raise notch.agent.errors.CommandError('CLI prompt not found prior '
                                                  'to sending command.')

        # Send the command.
        self.write(command + command_trailer)

        # Expect the command to be echoed back first, perhaps. If the
        # device echoes back the 'full' command for an abbreviated
        # command input (um, thanks), allow for that, also.
        if expect_command:
            i = self.expect(
                [re.escape(command) + expect_trailer, pexpect.EOF,
                 pexpect.TIMEOUT], timeout_short)
        else:
            trailer = expect_trailer or os.linesep
            i = self.expect([trailer, pexpect.EOF, pexpect.TIMEOUT],
                            timeout_short)
        if i > 0:
            exc = notch.agent.errors.CommandError(
                'Device did not start response within short response timeout.')
            exc.retry = True
            raise exc

        # Wait for the remaining data, possibly including pagers

        response_buf = []
        while True:
            if pager:
                i = self.expect([pager,
                                 esc_prompt, pexpect.EOF, pexpect.TIMEOUT],
                                timeout_long)
            else:
                i = self.expect([esc_prompt, pexpect.EOF, pexpect.TIMEOUT],
                                timeout_long)
                i += 1

            if i == 0:
                # Pager found.
                if self.strip_ansi:
                    response_buf.append(self._strip_ansi(self.before))
                else:
                    response_buf.append(self.before)
                self.write(pager_response)
            elif i == 2:
                exc = notch.agent.errors.CommandError(
                    'EOF received during command %r' % command)
                exc.retry = True
                raise exc
            elif i == 3:
                # Don't retry timeouts on the whole command - they usually
                # indicate overloaded devices.
                raise notch.agent.errors.CommandError(
                    'Command executed, CLI prompt not seen after %.1f sec' %
                    timeout_long)
            else:
                # Clean up the output to include only the part between the first
                # character after the newline after the command requested until
                # the last character prior to the next CLI prompt.
                prompt_index = self.before.rfind(prompt)
                if prompt_index == -1:
                    response_buf.append(self.before)
                else:
                    response_buf.append(self.before[:prompt_index])
                return ''.join(response_buf)