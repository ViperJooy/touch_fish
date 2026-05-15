"""Windows 窗口管理器"""
import subprocess
import time
import os
from typing import Optional, Any
from .base import BaseWindowManager
from src.utils.logger import logger

try:
    import win32gui
    import win32con
    import win32process
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    logger.warning("Windows 窗口管理库不可用")


class WindowsWindowManager(BaseWindowManager):
    """Windows 窗口管理器"""

    def __init__(self, config: dict):
        """初始化 Windows 窗口管理器

        Args:
            config: 配置字典
        """
        super().__init__(config)
        if not WINDOWS_AVAILABLE:
            logger.error("Windows 窗口管理库不可用，无法初始化")

    def get_active_window(self) -> Optional[Any]:
        """获取当前活动窗口

        Returns:
            窗口信息字典或 None
        """
        if not WINDOWS_AVAILABLE:
            return None

        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)

                return {
                    'hwnd': hwnd,
                    'title': title,
                    'pid': pid
                }
        except Exception as e:
            logger.error(f"获取活动窗口失败: {e}")

        return None

    def find_target_window(self) -> Optional[Any]:
        """查找目标应用窗口

        Returns:
            目标应用窗口信息或 None
        """
        if not WINDOWS_AVAILABLE:
            return None

        target_name = self._target_app
        target_window = [None]

        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if target_name.lower() in title.lower():
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    target_window[0] = {
                        'hwnd': hwnd,
                        'title': title,
                        'pid': pid
                    }
                    return False
            return True

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
            return target_window[0]
        except Exception as e:
            logger.error(f"查找目标应用窗口失败: {e}")
            return None

    def activate_window(self, window: Any) -> bool:
        """激活指定窗口

        Args:
            window: 窗口信息字典

        Returns:
            是否成功激活
        """
        if not WINDOWS_AVAILABLE:
            return False

        if not window or 'hwnd' not in window:
            logger.warning("窗口对象无效，无法激活")
            return False

        try:
            hwnd = window['hwnd']

            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            win32gui.SetForegroundWindow(hwnd)
            logger.info(f"成功激活窗口: {window.get('title', 'Unknown')}")
            return True

        except Exception as e:
            logger.error(f"激活窗口失败: {e}")
            return False

    def launch_target_app(self) -> bool:
        """启动目标应用

        Returns:
            是否成功启动
        """
        target_name = self._target_app

        try:
            logger.info(f"尝试启动目标应用: {target_name}")
            result = subprocess.run(
                ['start', target_name],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            if result.returncode == 0:
                logger.info(f"目标应用启动成功: {target_name}")
                time.sleep(2)
                return True

            logger.error(f"无法启动目标应用: {target_name}")
            return False

        except Exception as e:
            logger.error(f"启动目标应用失败: {e}")
            return False

    def is_window_valid(self, window: Any) -> bool:
        """检查窗口是否仍然有效

        Args:
            window: 窗口信息字典

        Returns:
            窗口是否有效
        """
        if not WINDOWS_AVAILABLE:
            return False

        if not window or 'hwnd' not in window:
            return False

        try:
            hwnd = window['hwnd']
            return win32gui.IsWindow(hwnd)
        except Exception as e:
            logger.error(f"检查窗口有效性失败: {e}")
            return False