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
        self._vscode_path = config.get("vscode_path", "auto")

    @abstractmethod
    def get_active_window(self) -> Optional[Any]:
        """获取当前活动窗口

        Returns:
            窗口对象或 None
        """
        pass

    @abstractmethod
    def find_vscode_window(self) -> Optional[Any]:
        """查找 VS Code 窗口

        Returns:
            VS Code 窗口对象或 None
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
    def launch_vscode(self) -> bool:
        """启动 VS Code

        Returns:
            是否成功启动
        """
        pass

    def activate_or_launch_vscode(self) -> bool:
        """激活或启动 VS Code

        Returns:
            是否成功
        """
        # 先尝试查找已运行的 VS Code 窗口
        vscode_window = self.find_vscode_window()
        if vscode_window:
            return self.activate_window(vscode_window)

        # 如果没有找到，尝试启动
        return self.launch_vscode()

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
