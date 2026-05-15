"""窗口管理器基类"""
from abc import ABC, abstractmethod
from typing import Optional, Any


class BaseWindowManager(ABC):
    """窗口管理器抽象基类"""

    def __init__(self, config: dict):
        """初始化窗口管理器

        Args:
            config: 配置字典
        """
        self._config = config
        self._target_app = config.get("target_app", "Visual Studio Code")

    @abstractmethod
    def get_active_window(self) -> Optional[Any]:
        """获取当前活动窗口

        Returns:
            窗口对象或 None
        """
        pass

    @abstractmethod
    def find_target_window(self) -> Optional[Any]:
        """查找目标应用窗口

        Returns:
            目标应用窗口对象或 None
        """
        pass

    @abstractmethod
    def activate_window(self, window: Any) -> bool:
        """激活指定窗口

        Args:
            window: 窗口对象

        Returns:
            是否成功激活
        """
        pass

    @abstractmethod
    def launch_target_app(self) -> bool:
        """启动目标应用

        Returns:
            是否成功启动
        """
        pass

    def activate_or_launch_target_app(self) -> bool:
        """激活或启动目标应用

        Returns:
            是否成功
        """
        from src.utils.logger import logger

        target_name = self._target_app

        target_window = self.find_target_window()
        if target_window:
            logger.info(f"找到运行中的 {target_name},尝试激活")
            if self.activate_window(target_window):
                return True
            logger.warning("激活失败,尝试重新启动")

        logger.info(f"启动 {target_name}")
        if not self.launch_target_app():
            logger.error(f"启动 {target_name} 失败")
            return False

        import time
        for i in range(3):
            time.sleep(1)
            logger.info(f"等待 {target_name} 启动... (尝试 {i+1}/3)")
            target_window = self.find_target_window()
            if target_window:
                logger.info(f"{target_name} 已启动,尝试激活")
                if self.activate_window(target_window):
                    return True

        logger.error(f"启动 {target_name} 后无法激活")
        return False

    @abstractmethod
    def is_window_valid(self, window: Any) -> bool:
        """检查窗口是否仍然有效

        Args:
            window: 窗口对象

        Returns:
            窗口是否有效
        """
        pass


class UnsupportedPlatformError(Exception):
    """不支持的平台错误"""
    pass