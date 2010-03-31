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

"""The Notch Session model.

A Session models the relationship between a particular common set of
request attributes (known as the session key) and a device connection.

This connection may be idle, disconnected, connected, or active.
The controller manages a cache of Session object instances,
keeping devices connected until idle timers expire.
"""


import collections
import logging
import threading
import time

import errors


# Used to uniquely identify a session.
SessionKey = collections.namedtuple(
    'SessionKey', 'device_name connect_method user privilege_level')


class Session(object):
    """A session manages a connections and requests to a device."""

    # Methods supported by the Device API that may be requested.
    valid_requests = ('command', 'get_config', 'set_config',
                      'copy_file', 'upload_file', 'download_file',
                      'delete_file', 'lock', 'unlock')

    def __init__(self, device=None):
        # TODO(afort): Allow devices to have multiple authentication
        # methods available (e.g., during password changes).
        self._exclusive = threading.Lock()

        self.device = device
        self._credential = None

        self._connected = False
        self.idle = True

        self.time_last_connect = None
        self.time_last_disconnect = None
        self.time_last_response = None
        self.time_last_request = None

        self._bytes_sent = 0
        self._bytes_recv = 0

        self._errors_connect = 0
        self._errors_disconnect = 0

    def __eq__(self, other):
        """Returns True if the other session manages the same device."""
        return bool(self.device == other.device)

    @property
    def connected(self):
        return self._connected

    @property
    def credential(self):
        return self._credential

    @credential.setter
    def credential(self, c):
        """Sets the session credential, re-connecting if presently connected."""
        try_to_reconnect = self._connected
        if c != self._credential:
            try:
                self.disconnect()
            except errors.Error, e:
                # Disconnection failed, update the cred and reconnect anyway.
                logging.error(str(e))
        self._credential = c

        if try_to_reconnect:
            try:
                self.connect()
            except errors.ConnectError:
                # If we aren'table to reconnect, it's no great loss.
                pass

    def connect(self):
        """Connects the session using a given Credential."""
        if self.device is None:
            return
        elif self._connected:
            return
        self.device.connect(credential=self._credential)
        self.time_last_connect = time.time()
        self._connected = True
        self.idle = True

    def disconnect(self):
        """Disconnects the session."""
        if self.device is None:
            return
        elif not self._connected:
            return
        self.device.disconnect()
        self.time_last_disconnect = time.time()
        self._connected = False
        self.idle = True

    def request(self, method, *args, **kwargs):
        """Executes a request on this session."""
        self._exclusive.acquire()
        try:
            # Check the method name is valid.
            if not method in self.valid_requests:
                raise errors.InvalidRequestError(
                    'Method %r not part of the device API.' % method)
            if self.device is None:
                raise errors.InvalidDeviceError('Device not yet initialised.')
            try:
                if not self._connected:
                    self.connect()
            except errors.ConnectError, e:
                return errors.handle(e)

            # Execute the method.
            self.time_last_request = time.time()
            device_method = getattr(self.device, method, None)
            if device_method is None:
                raise errors.InvalidRequestError(
                    'Method %r not part of the device API.' % method)

            self.idle = False
            try:
                # Remove the device_name argument not used in device.py.
                # TODO(afort): device.py/subclasses to take **kwargs instead?
                if 'device_name' in kwargs:
                    del kwargs['device_name']
                try:
                    result = device_method(*args, **kwargs)
                except errors.ApiError:
                    self.disconnect()
                    raise
                else:
                    self.time_last_response = time.time()
                    return result
            finally:
                self.idle = True
        finally:
            self._exclusive.release()
