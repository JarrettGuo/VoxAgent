#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : __init__.py.py
"""

from .file_operations_schemas import (
    FileReadSchema,
    FileWriteSchema,
    FileAppendSchema,
    FileDeleteSchema,
    FileSearchSchema,
    FileListSchema,
    FileCreateSchema,
    FileFindRecentSchema,
)
from .macos_schemas import (
    MailSearchSchema,
    MailReadSchema,
    MailSendSchema,
    MusicPlaySchema,
    MusicControlSchema,
    MusicSearchSchema,
)
from .schemas import (
    AppControlSchema,
    DuckDuckGoSearchSchema,
    WikipediaSearchSchema,
    GaodeWeatherSchema,
    Dalle3Schema,
    GoogleSerperSchema,
)

__all__ = [
    "AppControlSchema",
    "FileCreateSchema",
    "DuckDuckGoSearchSchema",
    "WikipediaSearchSchema",
    "GaodeWeatherSchema",
    "Dalle3Schema",
    "MailSearchSchema",
    "MailReadSchema",
    "FileReadSchema",
    "FileWriteSchema",
    "FileAppendSchema",
    "FileDeleteSchema",
    "FileSearchSchema",
    "FileListSchema",
    "FileFindRecentSchema",
    "MailSendSchema",
    "MusicPlaySchema",
    "MusicControlSchema",
    "MusicSearchSchema",
    "GoogleSerperSchema",
]
