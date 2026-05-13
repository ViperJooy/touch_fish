"""窗口管理器工厂"""
import platform
from .base import BaseWindowManager, UnsupportedPlatformError
from src.utils.logger import logger


def create_window_manager(config: dict) -> BaseWindowManager:
    """创建适合当前平台的窗口管理器

    Args:
        config: 配置字典

    Returns:
        窗口管理器实例

    Raises:
        UnsupportedPlatformError: 不支持的平台
    """
    system = platform.system()

    if system == "Darwin":
        logger.info("检测到 macOS 平台，使用 macOS 窗口管理器")
        from .macos import MacOSWindowManager
        return MacOSWindowManager(config)

    elif system == "Windows":
        logger.info("检测到 Windows 平台，使用 Windows 窗口管理器")
        from .windows import WindowsWindowManager
        return WindowsWindowManager(config)

    else:
        error_msg = f"不支持的平台: {system}"
        logger.error(error_msg)
        raise UnsupportedPlatformError(error_msg)
