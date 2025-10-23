#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : __init__.py.py
"""

from .duckduckgo import duckduckgo_search
from .wikipedia import wikipedia_search

__all__ = [
    "duckduckgo_search",
    "wikipedia_search",
]
