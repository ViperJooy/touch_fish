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

    def find_vscode_window(self) -> Optional[Any]:
        """查找 VS Code 窗口

        Returns:
            VS Code 窗口信息或 None
        """
        if not WINDOWS_AVAILABLE:
            return None

        vscode_window = [None]

        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                # VS Code 窗口标题通常包含 "Visual Studio Code"
                if 'Visual Studio Code' in title or title.endswith('- Visual Studio Code'):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    vscode_window[0] = {
                        'hwnd': hwnd,
                        'title': title,
                        'pid': pid
                    }
                    return False  # 停止枚举
            return True

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
            return vscode_window[0]
        except Exception as e:
            logger.error(f"查找 VS Code 窗口失败: {e}")
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

            # 如果窗口最小化，先恢复
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # 激活窗口
            win32gui.SetForegroundWindow(hwnd)
            logger.info(f"成功激活窗口: {window.get('title', 'Unknown')}")
            return True

        except Exception as e:
            logger.error(f"激活窗口失败: {e}")
            return False

    def launch_vscode(self) -> bool:
        """启动 VS Code

        Returns:
            是否成功启动
        """
        try:
            # 如果配置了具体路径
            if self._vscode_path and self._vscode_path != "auto":
                logger.info(f"使用配置的路径启动 VS Code: {self._vscode_path}")
                subprocess.Popen([self._vscode_path])
                time.sleep(2)  # 等待应用启动
                return True

            # 尝试常见的安装路径
            common_paths = [
                os.path.expandvars(r'%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe'),
                os.path.expandvars(r'%PROGRAMFILES%\Microsoft VS Code\Code.exe'),
                os.path.expandvars(r'%PROGRAMFILES(X86)%\Microsoft VS Code\Code.exe'),
            ]

            for path in common_paths:
                if os.path.exists(path):
                    logger.info(f"找到 VS Code: {path}")
                    subprocess.Popen([path])
                    time.sleep(2)  # 等待应用启动
                    return True

            # 尝试使用 code 命令
            logger.info("尝试使用 code 命令启动 VS Code")
            result = subprocess.run(
                ['code'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info("VS Code 启动成功")
                time.sleep(2)
                return True

            logger.error("无法启动 VS Code")
            return False

        except Exception as e:
            logger.error(f"启动 VS Code 失败: {e}")
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
            # 检查窗口句柄是否仍然有效
            return win32gui.IsWindow(hwnd)
        except Exception as e:
            logger.error(f"检查窗口有效性失败: {e}")
            return False
