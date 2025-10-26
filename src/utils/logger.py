import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "VoiceAssistant", level: str = "INFO", enable_file_logging: bool = True) -> logging.Logger:
    """设置日志记录器 - 兼容开发和生产环境"""
    try:
        import colorlog
        HAS_COLORLOG = True
    except ImportError:
        HAS_COLORLOG = False

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    if logger.handlers:
        return logger

    # 检测是否为打包后的应用
    is_frozen = getattr(sys, 'frozen', False)

    if is_frozen:
        app_dir = Path(sys.executable).parent
        logger.setLevel(getattr(logging, "WARNING"))
        enable_file_logging = True
    else:
        app_dir = Path(__file__).parent

    # === 控制台Handler ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    if HAS_COLORLOG and not is_frozen:
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # === 文件Handler (生产环境) ===
    if enable_file_logging:
        from logging.handlers import RotatingFileHandler

        log_dir = app_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logger.info("=" * 50)
        logger.info(f"应用启动 / Application started")
        logger.info(f"日志文件: {log_file}")
        logger.info("=" * 50)

    return logger


# 全局日志实例
logger = setup_logger()