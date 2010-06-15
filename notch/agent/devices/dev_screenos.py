#!/usr/bin/env python
#
# Copyright 2010 Andrew Fort. All Rights Reserved.
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

"""Notch device model for Netscreen ScreenOS operating system."""

import dev_ios


class ScreenOsDevice(dev_ios.IosDevice):
    """Netscreen ScreenOS device.

    Connect methods supported:
      sshv2 (via Paramiko in interactive mode with pexpect)
      telnet (via telnetlib)
    """

    LOGIN_PROMPT = 'sername:'
    PASSWORD_PROMPT = 'assword:'
    PROMPT = re.compile(r'\S+\s?->')

    ENABLE_CHAR = '#'

    DEFAULT_CONNECT_METHOD = 'sshv2'

