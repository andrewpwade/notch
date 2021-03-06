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

"""Notch device model for Nortel Passport/ESR devices.

This module presently uses the IOS device support as a basis.
SSH support is as yet untested.
"""


import logging
import re

import pexpect

import notch.agent.errors

import dev_ios


class EsrDevice(dev_ios.IosDevice):
    """A Nortel Passport/Ethernet Switch Router class device model.

    This model is used on devices like the Passport 8000 series and
    Passport/ERS 1600 models (though the Passport 1600 cannot display
    its config from the CLI, the ERS1624 can).
    """

    LOGIN_PROMPT = 'Login:'
    PROMPT = re.compile(r'.+\s?[$>\#]')

    def _disconnect(self):
        try:
            self._transport.write('logout\n')
        except (notch.agent.errors.CommandError,
                OSError, EOFError, pexpect.EOF):
            return
        else:
            self._transport.disconnect()

    def _disable_pager(self):
        logging.debug('Disabling pager on %r', self.name)
        self._transport.command('config cli more false', self._prompt)
        logging.debug('Disabled pager on %r', self.name)

    def __init__(self, name=None, addresses=None):
        super(EsrDevice, self).__init__(name=name, addresses=addresses)

    def _connect(self, address=None, port=None,
                 connect_method=None, credential=None):
        super(EsrDevice, self)._connect(address=address,
                                        port=port,
                                        connect_method=connect_method,
                                        credential=credential)
        self._transport.strip_ansi = True
        self._transport.dos2unix = True

    def _enable(self, enable_password):
        logging.debug('ESR device %r cannot be enabled.', self.name)
