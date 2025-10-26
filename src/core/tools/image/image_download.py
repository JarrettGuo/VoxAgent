import time
from typing import Type, Optional

import requests
from pathlib import Path
from langchain_core.tools import BaseTool

from src.core.tools.base.schemas import ImageDownloadSchema


class ImageDownloadTool(BaseTool):
    name: str = "download_image"
    description: str = "下载图片到本地桌面。需要提供图片的URL，可选提供文件名。"
    args_schema: Type[ImageDownloadSchema] = ImageDownloadSchema

    def _run(
            self,
            url: str,
            filename: Optional[str] = None,
    ) -> str:
        """下载图片到桌面"""
        try:
            # 如果没有提供文件名，自动生成
            if not filename:
                filename = f"generated_image_{int(time.time())}.png"

            # 获取桌面路径（跨平台兼容）
            desktop = Path.home() / "Desktop"
            if not desktop.exists():
                desktop = Path.home() / "桌面"
                if not desktop.exists():
                    desktop = Path.home()

            # 完整保存路径
            save_path = desktop / filename

            # 下载图片
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # 保存到桌面
            with open(save_path, 'wb') as f:
                f.write(response.content)

            return f"✅ 图片已成功下载到桌面：{save_path}"

        except Exception as e:
            return f"❌ 下载失败：{str(e)}"

    async def _arun(
            self,
            url: str,
            filename: Optional[str] = None,
    ) -> str:
        """异步版本"""
        return self._run(url, filename)

def image_download() -> BaseTool:
    """工厂函数：创建图片下载工具"""
    return ImageDownloadTool()