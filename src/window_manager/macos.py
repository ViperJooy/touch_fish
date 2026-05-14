"""macOS 窗口管理器"""
import subprocess
import time
from typing import Optional, Any
from .base import BaseWindowManager
from src.utils.logger import logger

try:
    from AppKit import NSWorkspace, NSRunningApplication
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    )
    MACOS_AVAILABLE = True
except ImportError:
    MACOS_AVAILABLE = False
    logger.warning("macOS 窗口管理库不可用")


class MacOSWindowManager(BaseWindowManager):
    """macOS 窗口管理器"""

    def __init__(self, config: dict):
        """初始化 macOS 窗口管理器

        Args:
            config: 配置字典
        """
        super().__init__(config)
        if not MACOS_AVAILABLE:
            logger.error("macOS 窗口管理库不可用，无法初始化")

    def get_active_window(self) -> Optional[Any]:
        """获取当前活动窗口

        Returns:
            窗口信息字典或 None
        """
        if not MACOS_AVAILABLE:
            return None

        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()

            if active_app:
                return {
                    'app_name': active_app.get('NSApplicationName', ''),
                    'bundle_id': active_app.get('NSApplicationBundleIdentifier', ''),
                    'pid': active_app.get('NSApplicationProcessIdentifier', 0)
                }
        except Exception as e:
            logger.error(f"获取活动窗口失败: {e}")

        return None

    def find_vscode_window(self) -> Optional[Any]:
        """查找 VS Code 窗口

        Returns:
            VS Code 窗口信息或 None
        """
        if not MACOS_AVAILABLE:
            logger.error("macOS 库不可用")
            return None

        try:
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()

            # 查找 VS Code 应用
            vscode_names = [
                'Visual Studio Code',
                'Code',
                'VSCode'
            ]

            vscode_bundle_ids = [
                'com.microsoft.VSCode',
                'com.visualstudio.code.oss'
            ]

            for app in running_apps:
                app_name = app.localizedName()
                bundle_id = app.bundleIdentifier()

                # 检查应用名称或 bundle ID
                if app_name in vscode_names or bundle_id in vscode_bundle_ids:
                    logger.info(f"找到 VS Code: {app_name} ({bundle_id})")
                    return {
                        'app_name': app_name,
                        'bundle_id': bundle_id,
                        'pid': app.processIdentifier(),
                        'app': app
                    }

            logger.info("未找到运行中的 VS Code")

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
        if not MACOS_AVAILABLE:
            logger.error("macOS 库不可用")
            return False

        if not window:
            logger.warning("窗口对象为空，无法激活")
            return False

        try:
            # 如果窗口信息包含 NSRunningApplication 对象
            if 'app' in window:
                logger.info(f"尝试激活窗口: {window.get('app_name', 'Unknown')}")
                app = window['app']

                # 尝试多次激活
                for attempt in range(2):
                    success = app.activateWithOptions_(1 << 1)  # NSApplicationActivateIgnoringOtherApps
                    if success:
                        logger.info(f"成功激活窗口: {window.get('app_name', 'Unknown')}")
                        time.sleep(0.3)  # 给系统一点时间切换
                        return True
                    logger.warning(f"激活尝试 {attempt+1} 失败,重试...")
                    time.sleep(0.2)

                logger.error(f"激活窗口失败 (所有尝试都失败): {window.get('app_name', 'Unknown')}")

            # 如果只有 bundle_id，尝试通过 bundle_id 激活
            elif 'bundle_id' in window:
                bundle_id = window['bundle_id']
                logger.info(f"尝试通过 bundle_id 激活: {bundle_id}")
                workspace = NSWorkspace.sharedWorkspace()
                success = workspace.launchAppWithBundleIdentifier_options_additionalEventParamDescriptor_launchIdentifier_(
                    bundle_id, 1 << 1, None, None
                )
                if success:
                    logger.info(f"成功激活应用: {bundle_id}")
                    time.sleep(0.3)
                    return True
                else:
                    logger.error(f"激活应用失败 (launchApp 返回 False): {bundle_id}")

            # 如果有应用名称，尝试使用 open 命令
            elif 'app_name' in window:
                app_name = window['app_name']
                logger.info(f"尝试使用 open 命令激活: {app_name}")
                result = subprocess.run(
                    ['open', '-a', app_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"成功激活应用: {app_name}")
                    time.sleep(0.3)
                    return True
                else:
                    logger.error(f"open 命令失败: {result.stderr}")

        except Exception as e:
            logger.error(f"激活窗口异常: {e}")
            logger.exception("详细错误:")

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
                result = subprocess.run(
                    ['open', '-a', self._vscode_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info("VS Code 启动成功")
                    time.sleep(1)  # 等待应用启动
                    return True
                else:
                    logger.error(f"启动失败: {result.stderr}")

            # 尝试常见的 VS Code 名称
            vscode_names = [
                'Visual Studio Code',
                'Code'
            ]

            for name in vscode_names:
                logger.info(f"尝试启动 VS Code: {name}")
                result = subprocess.run(
                    ['open', '-a', name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    logger.info(f"VS Code 启动成功: {name}")
                    time.sleep(1)  # 等待应用启动
                    return True
                else:
                    logger.warning(f"启动 {name} 失败: {result.stderr}")

            logger.error("无法启动 VS Code - 所有尝试都失败了")
            return False

        except Exception as e:
            logger.error(f"启动 VS Code 异常: {e}")
            logger.exception("详细错误:")
            return False

    def is_window_valid(self, window: Any) -> bool:
        """检查窗口是否仍然有效

        Args:
            window: 窗口信息字典

        Returns:
            窗口是否有效
        """
        if not window:
            return False

        try:
            # 如果有 PID，检查进程是否还在运行
            if 'pid' in window:
                pid = window['pid']
                workspace = NSWorkspace.sharedWorkspace()
                running_apps = workspace.runningApplications()

                for app in running_apps:
                    if app.processIdentifier() == pid:
                        return True

            # 如果有 bundle_id，检查应用是否在运行
            if 'bundle_id' in window:
                bundle_id = window['bundle_id']
                workspace = NSWorkspace.sharedWorkspace()
                running_apps = workspace.runningApplications()

                for app in running_apps:
                    if app.bundleIdentifier() == bundle_id:
                        return True

        except Exception as e:
            logger.error(f"检查窗口有效性失败: {e}")

        return False
