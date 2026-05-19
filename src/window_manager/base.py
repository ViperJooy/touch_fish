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
        self._target_apps = config.get("target_apps", [
            {"min_faces": 1, "app": "Google Chrome"},
            {"min_faces": 2, "app": "Visual Studio Code"}
        ])
        self._target_entry = self._target_apps[0]
        self._target_app = self._target_apps[0]["app"]
        self._launch_command = self._target_apps[0].get("launch_command")

    def set_target_app(self, app_name_or_entry):
        """设置当前目标应用

        Args:
            app_name_or_entry: 应用名称（字符串）或配置条目（字典，含 app 和可选 launch_command）
        """
        if isinstance(app_name_or_entry, dict):
            self._target_entry = app_name_or_entry
            self._target_app = app_name_or_entry["app"]
            self._launch_command = app_name_or_entry.get("launch_command")
        else:
            self._target_app = app_name_or_entry
            self._launch_command = None
            for entry in self._target_apps:
                if entry["app"] == app_name_or_entry:
                    self._target_entry = entry
                    self._launch_command = entry.get("launch_command")
                    break

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
            if self.activate_window(target_window):
                return True

        if not self.launch_target_app():
            return False

        import time
        for i in range(3):
            time.sleep(1)
            target_window = self.find_target_window()
            if target_window:
                if self.activate_window(target_window):
                    return True

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