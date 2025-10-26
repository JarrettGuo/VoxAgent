import threading
from pathlib import Path
import platform
from typing import Optional, List

import pygame

class MusicPlayer:
    """跨平台音乐播放器（单例模式）"""

    _instance = None
    _lock = threading.Lock()

    # 支持的音频格式
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']

    def __init__(self):
        if MusicPlayer._instance is not None:
            raise Exception("This is a singleton class!")

        pygame.mixer.init()
        self.current_song: Optional[Path] = None
        self.playlist: List[Path] = []
        self.current_index: int = -1
        self.is_paused: bool = False
        self.music_library: List[Path] = []
        self._index_music_library()

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _get_music_directories(self) -> List[Path]:
        """获取默认音乐目录"""
        system = platform.system()
        home = Path.home()

        if system == "Windows":
            dirs = [
                home / "Music",
                Path("C:/Users/Public/Music") if Path("C:/Users/Public/Music").exists() else None
            ]
        elif system == "Darwin":  # macOS
            dirs = [
                home / "Music",
                home / "Downloads"
            ]
        else:  # Linux
            dirs = [
                home / "Music",
                home / "Downloads"
            ]

        return [d for d in dirs if d and d.exists()]

    def _index_music_library(self):
        """索引音乐库"""
        self.music_library = []
        music_dirs = self._get_music_directories()

        for music_dir in music_dirs:
            for file_path in music_dir.rglob("*"):
                if file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                    self.music_library.append(file_path)

        print(f"音乐库已索引: 找到 {len(self.music_library)} 首歌曲")

    def search(self, query: str, limit: int = 5) -> List[Path]:
        """搜索音乐文件"""
        query_lower = query.lower()
        results = []

        for file_path in self.music_library:
            # 搜索文件名（不含扩展名）
            if query_lower in file_path.stem.lower():
                results.append(file_path)
                if len(results) >= limit:
                    break

        return results

    def play(self, file_path: Path) -> str:
        """播放指定音乐文件"""
        try:
            if not file_path.exists():
                return f"文件不存在: {file_path}"

            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()
            self.current_song = file_path
            self.is_paused = False

            return f"正在播放: {file_path.stem}"

        except Exception as e:
            return f"播放失败: {str(e)}"

    def pause(self) -> str:
        """暂停播放"""
        if pygame.mixer.music.get_busy() and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            return "已暂停"
        return "当前没有正在播放的音乐"

    def resume(self) -> str:
        """恢复播放"""
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            return f"继续播放: {self.current_song.stem if self.current_song else '未知'}"
        return "当前没有暂停的音乐"

    def stop(self) -> str:
        """停止播放"""
        pygame.mixer.music.stop()
        self.is_paused = False
        result = f"已停止播放: {self.current_song.stem if self.current_song else '未知'}"
        self.current_song = None
        return result

    def get_current_status(self) -> str:
        """获取当前播放状态"""
        if self.current_song is None:
            return "当前没有播放音乐"

        if self.is_paused:
            return f"已暂停: {self.current_song.stem}"

        if pygame.mixer.music.get_busy():
            return f"正在播放: {self.current_song.stem}"

        return f"当前歌曲: {self.current_song.stem} (已结束)"