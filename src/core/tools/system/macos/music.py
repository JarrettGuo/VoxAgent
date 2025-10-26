#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/22/25
@Author : guojarrett@gmail.com
@File   : music.py
"""

from typing import Any, Type

from src.core.tools.base import MusicPlaySchema, MusicControlSchema, MusicSearchSchema
from src.core.tools.system.macos.base import MacOSBaseTool, AppleScriptError
from src.utils.logger import logger


class MusicPlayTool(MacOSBaseTool):
    """音乐播放工具"""

    name: str = "music_play"
    description: str = (
        "在 Apple Music 中搜索并播放指定歌曲。"
        "输入歌曲名称，系统会搜索并播放最匹配的结果。"
    )
    args_schema: Type[MusicPlaySchema] = MusicPlaySchema

    def _run(self, song_name: str, **kwargs: Any) -> str:
        """播放音乐"""
        try:
            if not self._ensure_app_running("Music"):
                return "无法启动 Music 应用"

            script = f'''
            tell application "Music"
                set searchResults to (search playlist 1 for "{song_name}")

                if (count of searchResults) > 0 then
                    set firstTrack to item 1 of searchResults
                    play firstTrack

                    set trackName to name of firstTrack
                    set trackArtist to artist of firstTrack

                    return "正在播放: " & trackName & " - " & trackArtist
                else
                    return "未找到歌曲: {song_name}"
                end if
            end tell
            '''

            result = self._execute_applescript(script)
            logger.info(f"播放音乐: {song_name}")

            return result

        except AppleScriptError as e:
            return self._format_error_response(e)


class MusicControlTool(MacOSBaseTool):
    """音乐控制工具"""

    name: str = "music_control"
    description: str = (
        "控制 Apple Music 的播放状态。"
        "支持播放、暂停、下一首、上一首、停止等操作。"
    )
    args_schema: Type[MusicControlSchema] = MusicControlSchema

    def _run(self, action: str, **kwargs: Any) -> str:
        """控制音乐播放"""
        try:
            if not self._ensure_app_running("Music"):
                return "无法启动 Music 应用"

            action_map = {
                "play": "play",
                "pause": "pause",
                "next": "next track",
                "previous": "previous track",
                "stop": "stop"
            }

            applescript_action = action_map.get(action)
            if not applescript_action:
                return f"不支持的操作: {action}"

            script = f'''
            tell application "Music"
                {applescript_action}

                if player state is playing then
                    set currentTrack to current track
                    set trackName to name of currentTrack
                    set trackArtist to artist of currentTrack
                    return "当前播放: " & trackName & " - " & trackArtist
                else
                    return "已{action}"
                end if
            end tell
            '''

            result = self._execute_applescript(script)
            logger.info(f"音乐控制: {action}")

            return result

        except AppleScriptError as e:
            return self._format_error_response(e)


class MusicSearchTool(MacOSBaseTool):
    """音乐搜索工具"""

    name: str = "music_search"
    description: str = "在 Apple Music 资料库中搜索歌曲"
    args_schema: Type[MusicSearchSchema] = MusicSearchSchema

    def _run(self, query: str, limit: int = 5, **kwargs: Any) -> str:
        """搜索音乐"""
        try:
            if not self._ensure_app_running("Music"):
                return "无法启动 Music 应用"

            # AppleScript 语法
            script = f'''
            tell application "Music"
                set searchResults to (search playlist 1 for "{query}")
                set resultList to {{}}
                set resultCount to count of searchResults

                if resultCount = 0 then
                    return "未找到匹配的歌曲"
                end if

                set maxCount to {limit}
                if resultCount < maxCount then
                    set maxCount to resultCount
                end if

                repeat with i from 1 to maxCount
                    set currentTrack to item i of searchResults
                    set trackName to name of currentTrack
                    set trackArtist to artist of currentTrack
                    set trackAlbum to album of currentTrack

                    set trackInfo to (i as string) & ". " & trackName & " - " & trackArtist & " (" & trackAlbum & ")"
                    set end of resultList to trackInfo
                end repeat

                set AppleScript's text item delimiters to linefeed
                set resultText to resultList as text
                set AppleScript's text item delimiters to ""

                return "搜索结果:" & linefeed & resultText
            end tell
            '''

            result = self._execute_applescript(script)
            return result

        except AppleScriptError as e:
            return self._format_error_response(e)


def music_play(**kwargs) -> MacOSBaseTool:
    """工厂函数：创建音乐播放工具"""
    return MusicPlayTool(**kwargs)


def music_control(**kwargs) -> MacOSBaseTool:
    """工厂函数：创建音乐控制工具"""
    return MusicControlTool(**kwargs)


def music_search(**kwargs) -> MacOSBaseTool:
    """工厂函数：创建音乐搜索工具"""
    return MusicSearchTool(**kwargs)
