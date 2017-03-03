#!/usr/bin/env python
# coding: utf-8
"""
    signals.py
    ~~~~~~~~~~

"""
from blinker import signal

signal_update_sidebar = signal("sidebar-update")
