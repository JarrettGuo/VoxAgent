#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/21/25
@Author : guojarrett@gmail.com
@File   : config.py.py
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        # 加载 .env 文件
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env"
        load_dotenv(dotenv_path=env_path, override=True)

        # 加载 config.yaml (仅用于非敏感配置)
        if config_path is None:
            config_path = project_root / "config" / "config.yaml"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """加载 YAML 配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return self._get_default_config()
        except Exception:
            return self._get_default_config()

    @classmethod
    def _get_default_config(cls) -> dict:
        """默认配置"""
        return {
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "chunk_size": 512,
                "format": "paInt16"
            },
            "wake_word": {
                "enabled": True,
                "keywords": ["computer", "jarvis"],
                "sensitivities": [0.5, 0.5],
                "silence_duration": 3.0
            },
            "logging": {
                "level": "DEBUG"
            },
            "asr": {
                "provider": "whisper",
                "whisper": {
                    "model": "openai/whisper-base",
                    "language": "zh"
                }
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        1. 先尝试从环境变量获取 (自动映射)
        2. 再从 YAML 配置获取
        """
        # 尝试从环境变量获取
        env_key = self._map_to_env_key(key)
        if env_key:
            env_value = os.getenv(env_key)
            if env_value is not None:
                return self._convert_type(env_value)

        # 从 YAML 配置获取
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def _map_to_env_key(self, yaml_key: str) -> Optional[str]:
        """映射 YAML 路径到环境变量名"""
        mapping = {
            # 唤醒词
            'wake_word.access_key': 'PORCUPINE_ACCESS_KEY',
            # LangSmith
            'langsmith.api_key': 'LANGSMITH_API_KEY',
            'langsmith.project': 'LANGSMITH_PROJECT',
            # API Keys
            'gaode_weather.api_key': 'GAODE_WEATHER_API_KEY',
            'openai.api_key': 'OPENAI_API_KEY',
            'google_serper.api_key': 'GOOGLE_SERPER_API_KEY',
            # 七牛云
            'qiniu.api_key': 'QINIU_API_KEY',
        }
        return mapping.get(yaml_key)

    def _convert_type(self, value: str) -> Any:
        """智能类型转换"""
        if not isinstance(value, str):
            return value

        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # 数字
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        return value


# 全局配置实例
config = Config()
