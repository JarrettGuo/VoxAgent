#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : config.py.py
"""

from pathlib import Path

import yaml


class Config:
    """配置管理类"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"配置文件不存在: {self.config_path}")
            return self._get_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self._get_default_config()

    @classmethod
    def _get_default_config(cls) -> dict:
        """默认配置"""
        return {
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "chunk_size": 1024
            },
            "wake_word": {
                "enabled": True,
                "keywords": ["ni hao yu yin zhu shou", "hello assistant"],
                "sensitivity": 0.5
            },
            "logging": {
                "level": "INFO"
            }
        }

    def get(self, key: str, default=None):
        """获取配置项，支持点号分隔的路径"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default


# 全局配置实例
config = Config()
