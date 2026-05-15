"""主控制器"""
import time
from typing import Optional
from src.utils.config import ConfigManager
from src.utils.logger import logger
from src.state_manager import StateManager, State
from src.window_manager import create_window_manager


class MainController:
    """主控制器，协调所有模块"""

    def __init__(self, config_path: str = "config.json"):
        """初始化主控制器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config_manager: Optional[ConfigManager] = None
        self.state_manager: Optional[StateManager] = None
        self.window_manager = None
        self.face_detector = None
        self.camera_monitor = None
        self.tray_icon = None
        self._running = False
        self._last_switch_attempt = 0  # 上次切换尝试的时间
        self._switch_cooldown = 3.0  # 切换失败后的冷却时间(秒)

    def initialize(self) -> bool:
        """初始化所有模块

        Returns:
            是否成功初始化
        """
        try:
            # 1. 加载配置
            logger.info("正在加载配置...")
            self.config_manager = ConfigManager(self.config_path)
            config = self.config_manager.load_config()

            # 2. 设置日志
            log_level = config.get("log_level", "INFO")
            logger.setup(log_level=log_level, log_file="logs/touch_fish_guard.log")
            logger.info("Touch Fish Guard 启动中...")

            # 3. 初始化状态管理器
            logger.info("初始化状态管理器...")
            self.state_manager = StateManager(config)

            # 4. 初始化窗口管理器
            logger.info("初始化窗口管理器...")
            self.window_manager = create_window_manager(config)

            # 5. 初始化人脸检测器
            logger.info("初始化人脸检测器...")
            try:
                from src.face_detector import FaceDetector
                self.face_detector = FaceDetector(config)
            except ImportError:
                logger.warning("人脸检测器不可用，使用假检测器")
                from src.fake_face_detector import FakeFaceDetector
                self.face_detector = FakeFaceDetector(config)

            # 6. 初始化摄像头监控器
            logger.info("初始化摄像头监控器...")
            from src.camera_monitor import CameraMonitor
            self.camera_monitor = CameraMonitor(
                config,
                self.face_detector,
                self._on_face_detection
            )

            # 7. 初始化托盘图标（如果可用）
            try:
                logger.info("初始化托盘图标...")
                from src.tray_icon import TrayIcon
                self.tray_icon = TrayIcon(self)
            except ImportError:
                logger.warning("托盘图标不可用")
                self.tray_icon = None

            logger.info("所有模块初始化完成")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            logger.exception("详细错误信息:")
            return False

    def start(self) -> bool:
        """启动应用

        Returns:
            是否成功启动
        """
        if not self.initialize():
            logger.error("初始化失败，无法启动")
            return False

        try:
            # 启动摄像头监控
            logger.info("启动摄像头监控...")
            if not self.camera_monitor.start_monitoring():
                logger.error("无法启动摄像头监控")
                self.state_manager.enter_error()
                return False

            self._running = True
            logger.info("Touch Fish Guard 已启动")

            # 如果有托盘图标，启动托盘
            if self.tray_icon:
                logger.info("启动托盘图标...")
                self.tray_icon.start()
            else:
                # 没有托盘图标时，保持主线程运行
                logger.info("进入主循环...")
                self._main_loop()

            return True

        except Exception as e:
            logger.error(f"启动失败: {e}")
            logger.exception("详细错误信息:")
            return False

    def _main_loop(self):
        """主循环（当没有托盘图标时使用）"""
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭...")
            self.shutdown()

    def _on_face_detection(self, face_count: int):
        """人脸检测回调

        Args:
            face_count: 检测到的人脸数量
        """
        try:
            # 如果处于暂停状态，忽略检测结果
            if self.state_manager.is_paused():
                return

            # 如果处于错误状态，忽略检测结果
            if self.state_manager.is_error():
                return

            current_state = self.state_manager.get_state()

            # 监控状态：检测到人脸时切换到目标应用
            if current_state == State.MONITORING:
                if face_count >= 1:
                    current_time = time.time()
                    if current_time - self._last_switch_attempt < self._switch_cooldown:
                        logger.debug(f"切换冷却中，跳过本次尝试")
                        return

                    logger.info(f"检测到 {face_count} 人，准备切换")
                    self._last_switch_attempt = current_time
                    self._switch_to_target(face_count)

            # 已切换状态：检测到单人或无人时考虑切回
            elif current_state == State.SWITCHED:
                if face_count <= 1:
                    # 更新切回确认
                    can_switch_back = self.state_manager.update_switch_back_confirmation(face_count)

                    if can_switch_back:
                        logger.info(f"连续检测通过，准备切回原窗口")
                        self._switch_back()
                    else:
                        progress = self.state_manager.get_switch_back_progress()
                        logger.debug(f"切回确认进度: {progress[0]}/{progress[1]}")
                else:
                    # 检测到多人，重置切回计数
                    self.state_manager.update_switch_back_confirmation(face_count)

        except Exception as e:
            logger.error(f"处理检测结果时出错: {e}")
            logger.exception("详细错误信息:")

    def _switch_to_target(self, face_count: int):
        """切换到目标应用

        Args:
            face_count: 当前检测到的人脸数量
        """
        try:
            config = self.config_manager._config
            target_apps = config.get("target_apps", [
                {"min_faces": 1, "app": "Google Chrome"},
                {"min_faces": 2, "app": "Visual Studio Code"}
            ])

            target_name = None
            for entry in reversed(target_apps):
                if face_count >= entry.get("min_faces", 1):
                    target_name = entry["app"]
                    break
            target_name = target_name or target_apps[-1]["app"]

            self.window_manager.set_target_app(target_name)

            current_window = self.window_manager.get_active_window()
            if current_window:
                self.state_manager.record_previous_window(current_window)
                logger.info(f"记录当前窗口: {current_window.get('app_name', current_window.get('title', 'Unknown'))}")

            success = self.window_manager.activate_or_launch_target_app()

            if success:
                self.state_manager.set_state(State.SWITCHED)
                self.state_manager.record_switch_time()
                logger.info(f"成功切换到 {target_name}")

                if self.tray_icon:
                    self.tray_icon.update_status(State.SWITCHED, 0)
            else:
                logger.error(f"切换到 {target_name} 失败")

        except Exception as e:
            logger.error(f"切换到目标应用时出错: {e}")
            logger.exception("详细错误信息:")

    def _switch_back(self):
        """切回原窗口"""
        try:
            previous_window = self.state_manager.get_previous_window()

            if not previous_window:
                logger.warning("没有记录的原窗口，回到监控状态")
                self.state_manager.set_state(State.MONITORING)
                if self.tray_icon:
                    self.tray_icon.update_status(State.MONITORING, 0)
                return

            # 检查原窗口是否仍然有效
            if not self.window_manager.is_window_valid(previous_window):
                logger.warning("原窗口已失效，回到监控状态")
                self.state_manager.set_state(State.MONITORING)
                if self.tray_icon:
                    self.tray_icon.update_status(State.MONITORING, 0)
                return

            # 激活原窗口
            success = self.window_manager.activate_window(previous_window)

            if success:
                logger.info("成功切回原窗口")
                self.state_manager.set_state(State.MONITORING)
                if self.tray_icon:
                    self.tray_icon.update_status(State.MONITORING, 0)
            else:
                logger.error("切回原窗口失败")

        except Exception as e:
            logger.error(f"切回原窗口时出错: {e}")
            logger.exception("详细错误信息:")

    def pause(self):
        """暂停监控"""
        logger.info("暂停监控")
        self.state_manager.pause()
        if self.tray_icon:
            self.tray_icon.update_status(State.PAUSED, 0)

    def resume(self):
        """恢复监控"""
        logger.info("恢复监控")
        self.state_manager.resume()
        if self.tray_icon:
            self.tray_icon.update_status(State.MONITORING, 0)

    def reload_config(self):
        """重新加载配置"""
        try:
            logger.info("重新加载配置...")
            config = self.config_manager.reload_config()

            # 更新日志级别
            log_level = config.get("log_level", "INFO")
            logger.setup(log_level=log_level, log_file="logs/touch_fish_guard.log")

            logger.info("配置重新加载完成")

        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            logger.exception("详细错误信息:")

    def shutdown(self):
        """关闭应用"""
        logger.info("正在关闭 Touch Fish Guard...")
        self._running = False

        # 停止摄像头监控
        if self.camera_monitor:
            self.camera_monitor.stop_monitoring()

        # 停止托盘图标
        if self.tray_icon:
            self.tray_icon.stop()

        logger.info("Touch Fish Guard 已关闭")

    def get_status(self) -> dict:
        """获取当前状态信息

        Returns:
            状态信息字典
        """
        if not self.state_manager or not self.camera_monitor:
            return {"status": "未初始化"}

        return {
            "state": self.state_manager.get_state_name(),
            "face_count": self.camera_monitor.current_face_count,
            "running": self._running
        }
