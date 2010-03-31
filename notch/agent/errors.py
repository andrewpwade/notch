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

"""Exceptions, error handlers and counters."""

import threading

# Mutex used to protect counters.
mu = threading.Lock()


# Error classes.

class Error(Exception):
    pass


class ConfigError(Error):
    """Configuration errors."""


class ConfigMissingRequiredSectionError(ConfigError):
    """The config was missing a required section."""


class CredentialError(Error):
    """Credential errors."""


class NoMatchingCredentialError(CredentialError):
    """There was nothing in the credentials store matching the hostname."""


class MissingFieldError(CredentialError):
    """The credential was missing a required field."""


class UnknownConfigurationFileFormatError(ConfigError):
    """The config file extension (and thus, format) was unrecognised."""


class UnknownCredentialsFileFormatError(CredentialError):
    """The file extension (and thus, format) was unrecognised."""


# Notch API error classes.

class ApiError(Error):
    """Errors emitted in response to an API call."""
    dampen_reconnect = False

    def __init__(self, *args, **kwargs):
        super(ApiError, self).__init__(*args, **kwargs)
        self.name = self.__class__.__name__
        self.msg = self.__class__.__doc__


class ConnectError(ApiError):
    """There was an error connecting to a device."""
    dampen_reconnect = True


class CommandError(ApiError):
    """There was an error whilst executing a command on a device."""


class DeviceWithoutAddressError(ApiError):
    """The device does not have an IP address."""


class DisconnectError(ApiError):
    """There was an error disconnecting from a device."""


class InvalidDeviceError(ApiError):
    """The device is not yet initialised."""


class InvalidModeError(ApiError):
    """The mode chosen for the API call was unsupported by the device."""


class InvalidRequestError(ApiError):
    """The method name being requested was not defined by the device API."""


class NoAddressesError(ApiError):
    """The device name has no addresses associated with it."""

    
class NoSuchDeviceError(ApiError):
    """The device name requested is not known to the system."""

    
class NoSuchVendorError(ApiError):
    """The vendor requested does not exist as a device model."""


class NoSessionCreatedError(ApiError):
    """No session could be created for the requested arguments."""


def tornadorpc_handle(exc):
    """Handles the exception for the tornadorpc framework and counts it."""




# Errors used in tornadorpc library for responses. Adds to existing JSON/XML
# RPC error codes. Key integers correspond to the 'code' attribute on ApiError
# sub-classes.

error_dictionary = {
    1: ConnectError,
    2: DisconnectError,
    3: InvalidDeviceError,
    4: InvalidModeError,
    5: InvalidRequestError,
    6: NoAddressesError,
    7: NoSuchVendorError,
    8: NoSessionCreatedError,
}
