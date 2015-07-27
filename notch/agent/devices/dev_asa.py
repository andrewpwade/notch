#!/usr/bin/env python

"""Notch device model for cisco ASA
"""

import dev_ios


class AsaDevice(dev_ios.IosDevice):
    """cisco ASA device model.
    """
    CMD_DISABLE_PAGING = 'terminal pager 0'
