"""日志模块"""
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


class Logger:
    """日志管理器"""

    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化日志器"""
        if self._logger is not None:
            return

        self._logger = logging.getLogger("TouchFishGuard")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def setup(self, log_level: str = "INFO", log_file: str = "logs/touch_fish_guard.log"):
        """设置日志器

        Args:
            log_level: 日志级别
            log_file: 日志文件路径
        """
        # 清除现有处理器
        self._logger.handlers.clear()

        # 设置日志级别
        level = getattr(logging, log_level.upper(), logging.INFO)
        self._logger.setLevel(level)

        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # 文件处理器 - 使用 RotatingFileHandler 避免日志文件过大
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

    def debug(self, message: str):
        """记录调试信息"""
        if self._logger:
            self._logger.debug(message)

    def info(self, message: str):
        """记录信息"""
        if self._logger:
            self._logger.info(message)

    def warning(self, message: str):
        """记录警告"""
        if self._logger:
            self._logger.warning(message)

    def error(self, message: str):
        """记录错误"""
        if self._logger:
            self._logger.error(message)

    def critical(self, message: str):
        """记录严重错误"""
        if self._logger:
            self._logger.critical(message)

    def exception(self, message: str):
        """记录异常"""
        if self._logger:
            self._logger.exception(message)


# 全局日志实例
logger = Logger()
