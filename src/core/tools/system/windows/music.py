from typing import Type, Any, Optional

from src.core.tools.base import PygameSearchSchema, PygameControlSchema, PygamePlaySchema
from src.core.tools.base.windows_schemas import PygameFetchSchema
from src.core.tools.system.windows.base import BaseMusicTool
from rapidfuzz import process


class MusicPlayTool(BaseMusicTool):
    """音乐播放工具"""

    name: str = "pygame_music_play"
    description: str = (
        "搜索并播放指定歌曲。"
        "输入歌曲名称，系统会在本地音乐库中搜索并播放最匹配的结果。"
    )
    args_schema: Type[PygamePlaySchema] = PygamePlaySchema

    def _run(self, song_name: str, **kwargs: Any) -> str:
        """播放音乐"""
        try:
            # 搜索歌曲
            results = self.player.search(song_name, limit=1)

            if not results:
                return f"未找到歌曲: {song_name}"

            # 播放第一个结果
            first_track = results[0]
            result = self.player.play(first_track)

            return result

        except Exception as e:
            return f"播放失败: {str(e)}"


class MusicControlTool(BaseMusicTool):
    """音乐控制工具"""

    name: str = "pygame_music_control"
    description: str = (
        "控制音乐播放状态。"
        "支持播放(play)、暂停(pause)、停止(stop)等操作。"
    )
    args_schema: Type[PygameControlSchema] = PygameControlSchema

    def _run(self, action: str, **kwargs: Any) -> str:
        """控制音乐播放"""
        try:
            action = action.lower()

            if action == "play":
                return self.player.resume()
            elif action == "pause":
                return self.player.pause()
            elif action == "stop":
                return self.player.stop()
            elif action == "status":
                return self.player.get_current_status()
            else:
                return f"不支持的操作: {action}。支持的操作: play, pause, stop, status"

        except Exception as e:
            return f"控制失败: {str(e)}"


class MusicSearchTool(BaseMusicTool):
    """音乐搜索工具"""

    name: str = "pygame_music_search"
    description: str = "搜索歌曲，必须先查询歌单后再使用"
    args_schema: Type[PygameSearchSchema] = PygameSearchSchema

    def _run(self, query: str, limit: int = 5, **kwargs: Any) -> str:
        """搜索音乐"""
        try:
            results = self.player.search(query, limit=limit)

            if not results:
                return "未找到匹配的歌曲"

            result_lines = ["搜索结果:"]
            for i, track in enumerate(results, 1):
                # 提取基本信息
                track_name = track.stem
                track_dir = track.parent.name

                result_lines.append(
                    f"{i}. {track_name} (位于: {track_dir})"
                )

            return "\n".join(result_lines)

        except Exception as e:
            return f"搜索失败: {str(e)}"


class MusicFetchTool(BaseMusicTool):
    """音乐搜索工具"""

    name: str = "pygame_music_fetch"
    description: str = "获取本地音乐库中的歌曲列表或根据歌名查询相近歌曲, 无论什么情况都先获取歌曲列表再确认搜索歌名"
    args_schema: Type[PygameFetchSchema] = PygameFetchSchema

    def _run(self, limit: int = 10, query: Optional[str] = None) -> str:
        """搜索音乐"""
        try:
            song_list = self.player.get_song_list()
            song_list = [str(song) for song in song_list]

            if query is None:
                result_lines = ["获取结果:"]
                for i, song_name in enumerate(song_list):
                    if i >= 20:
                        break
                    result_lines.append(
                        f"{i}. {song_name}"
                    )
                return "\n".join(result_lines)

            results = process.extract(
                query=query,
                choices=song_list,
                limit=limit
            )
            if not results:
                return "未找到歌曲"

            result_lines = ["获取结果:"]
            for i, song_name in enumerate(results):
                result_lines.append(
                    f"{i}. {song_name}"
                )

            return "\n".join(result_lines)

        except Exception as e:
            return f"获取失败: {str(e)}"


# Factory Functions
def pygame_music_play(**kwargs) -> BaseMusicTool:
    """工厂函数：创建音乐播放工具"""
    return MusicPlayTool(**kwargs)


def pygame_music_control(**kwargs) -> BaseMusicTool:
    """工厂函数：创建音乐控制工具"""
    return MusicControlTool(**kwargs)


def pygame_music_search(**kwargs) -> BaseMusicTool:
    """工厂函数：创建音乐搜索工具"""
    return MusicSearchTool(**kwargs)


def pygame_music_fetch(**kwargs) -> BaseMusicTool:
    """工厂函数：创建音乐搜索工具"""
    return MusicFetchTool(**kwargs)