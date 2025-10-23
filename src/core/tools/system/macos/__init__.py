#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : __init__.py.py
"""

from .base import MacOSBaseTool, AppleScriptError
from .mail import mail_search, mail_read, mail_send
from .music import music_play, music_control, music_search

__all__ = [
    "MacOSBaseTool",
    "AppleScriptError",
    "mail_search",
    "mail_read",
    "mail_send",
    "music_play",
    "music_control",
    "music_search",
]
