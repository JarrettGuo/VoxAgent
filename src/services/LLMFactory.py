#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 10/25/25
@Author : guojarrett@gmail.com
@File   : LLMFactory.py
"""

from typing import Dict

from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI

from src.utils.config import config
from src.utils.logger import logger


class LLMFactory:
    """
    LLM 工厂类 - 根据用途创建不同的模型

    分级策略：
    - Planner:  qwen3-max (最强推理)
    - Worker:   qwen3-max-preview (快速响应)
    - Summary:  qwen3-max-preview (快速总结)
    """

    _instances: Dict[str, ChatOpenAI] = {}

    @classmethod
    def get_llm(cls, llm_type: str = "worker") -> ChatOpenAI:
        """
        获取 LLM 实例（单例模式）

        Args:
            llm_type: planner | worker | summary

        Returns:
            ChatOpenAI 实例
        """
        # 检查缓存
        if llm_type in cls._instances:
            logger.debug(f"Using cached {llm_type} LLM")
            return cls._instances[llm_type]

        # 获取基础配置
        qiniu_config = config.get("qiniu")
        if not qiniu_config:
            raise ValueError("Qiniu config not found")

        # 获取模型特定配置
        model_config = config.get(f"qiniu.models.{llm_type}")

        if not model_config:
            logger.warning(
                f"No specific config for {llm_type}, using default worker config"
            )
            model_config = {
                "model": "qwen3-max-preview",
                "temperature": 0.0,
                "max_tokens": 500
            }

        # 创建实例
        llm = ChatOpenAI(
            api_key=qiniu_config.get("api_key"),
            base_url=qiniu_config.get("base_url"),
            model=model_config.get("model"),
            temperature=model_config.get("temperature", 0.0),
            max_tokens=model_config.get("max_tokens", 500),
        )

        # 缓存实例
        cls._instances[llm_type] = llm

        logger.info(
            f"✅ Created {llm_type} LLM: "
            f"model={model_config.get('model')}, "
            f"temp={model_config.get('temperature')}, "
            f"max_tokens={model_config.get('max_tokens')}"
        )

        return llm

    @classmethod
    def _create_ollama_llm(cls) -> ChatOllama:
        """创建 Ollama 本地模型（用于 Worker）"""
        try:
            ollama_config = config.get("ollama", {})

            if not ollama_config.get("enabled", False):
                raise ValueError("Ollama is not enabled in config")

            model_name = ollama_config.get("model", "qwen2.5:7b")
            base_url = ollama_config.get("base_url", "http://localhost:11434")
            temperature = ollama_config.get("temperature", 0.0)
            timeout = ollama_config.get("timeout", 60)

            llm = ChatOllama(
                model=model_name,
                base_url=base_url,
                temperature=temperature,
                timeout=timeout,
                # 启用工具调用支持
                num_ctx=4096,  # 上下文长度
            )

            logger.info(
                f"✅ Created Worker Ollama LLM: "
                f"model={model_name}, "
                f"temp={temperature}, "
                f"base_url={base_url}"
            )

            return llm

        except Exception as e:
            logger.error(f"Failed to create Ollama LLM: {e}")
            logger.warning("⚠️  Falling back to Qiniu cloud for Worker")
            # 降级到七牛云
            return cls._create_qiniu_llm("worker")

    @classmethod
    def _create_qiniu_llm(cls, llm_type: str) -> ChatOpenAI:
        """创建七牛云 LLM（用于 Planner 和 Summary）"""
        try:
            # 获取基础配置
            qiniu_config = config.get("qiniu")
            if not qiniu_config:
                raise ValueError("Qiniu config not found")

            # 获取模型特定配置
            model_config = config.get(f"qiniu.models.{llm_type}")

            if not model_config:
                logger.warning(
                    f"No specific config for {llm_type}, using default config"
                )
                model_config = {
                    "model": "doubao-1.5-pro-32k",
                    "temperature": 0.0,
                    "max_tokens": 500
                }

            # 创建实例
            llm = ChatOpenAI(
                api_key=qiniu_config.get("api_key"),
                base_url=qiniu_config.get("base_url"),
                model=model_config.get("model"),
                temperature=model_config.get("temperature", 0.0),
                max_tokens=model_config.get("max_tokens", 500),
            )

            logger.info(
                f"✅ Created {llm_type} Qiniu LLM: "
                f"model={model_config.get('model')}, "
                f"temp={model_config.get('temperature')}, "
                f"max_tokens={model_config.get('max_tokens')}"
            )

            return llm

        except Exception as e:
            logger.error(f"Failed to create Qiniu LLM for {llm_type}: {e}")
            raise

    @classmethod
    def get_planner_llm(cls) -> ChatOpenAI:
        """
        获取 Planner 专用 LLM

        使用 qwen3-max：最强推理能力，用于任务规划
        """
        return cls.get_llm("planner")

    @classmethod
    def get_worker_llm(cls) -> ChatOpenAI:
        """
        获取 Worker 专用 LLM

        使用 qwen3-max-preview：快速响应，用于工具调用
        """
        return cls.get_llm("worker")

    @classmethod
    def get_summary_llm(cls) -> ChatOpenAI:
        """
        获取 Summary 专用 LLM

        使用 qwen3-max-preview：快速响应，用于结果总结
        """
        return cls.get_llm("summary")

    @classmethod
    def get_model_info(cls, llm_type: str) -> Dict[str, any]:
        """获取模型配置信息"""
        model_config = config.get(f"qiniu.models.{llm_type}")
        return {
            "type": llm_type,
            "model": model_config.get("model"),
            "temperature": model_config.get("temperature"),
            "max_tokens": model_config.get("max_tokens")
        }

    @classmethod
    def clear_cache(cls):
        """清除缓存（用于测试或重新配置）"""
        cls._instances.clear()
        logger.info("🗑️  LLM cache cleared")

    @classmethod
    def get_all_models_info(cls) -> Dict[str, Dict]:
        """获取所有模型配置信息"""
        return {
            "planner": cls.get_model_info("planner"),
            "worker": cls.get_model_info("worker"),
            "summary": cls.get_model_info("summary")
        }
