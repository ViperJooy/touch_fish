"""系统托盘图标"""
import os
import sys
from typing import Optional
from src.state_manager import State
from src.utils.logger import logger

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    logger.warning("托盘图标库不可用")


class TrayIcon:
    """系统托盘图标"""

    def __init__(self, controller):
        """初始化托盘图标

        Args:
            controller: 主控制器实例
        """
        if not TRAY_AVAILABLE:
            logger.error("托盘图标库不可用")
            raise ImportError("pystray 或 PIL 不可用")

        self._controller = controller
        self._icon: Optional[pystray.Icon] = None
        self._current_state = State.MONITORING
        self._face_count = 0

    def start(self):
        """启动托盘图标"""
        try:
            # 创建图标
            icon_image = self._create_icon_image(State.MONITORING)

            # 创建菜单
            menu = pystray.Menu(
                pystray.MenuItem("Touch Fish Guard", self._show_status, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    lambda text: f"状态: {self._controller.state_manager.get_state_name()}",
                    self._show_status,
                    enabled=False
                ),
                pystray.MenuItem(
                    lambda text: f"检测到: {self._face_count} 人",
                    self._show_status,
                    enabled=False
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "暂停",
                    self._toggle_pause,
                    checked=lambda item: self._controller.state_manager.is_paused()
                ),
                pystray.MenuItem("打开配置文件", self._open_config),
                pystray.MenuItem("重新加载配置", self._reload_config),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("关于", self._show_about),
                pystray.MenuItem("退出", self._quit)
            )

            # 创建托盘图标
            self._icon = pystray.Icon(
                "TouchFishGuard",
                icon_image,
                "Touch Fish Guard",
                menu
            )

            logger.info("托盘图标已创建，准备运行")

            # 运行托盘图标（这会阻塞主线程）
            self._icon.run()

        except Exception as e:
            logger.error(f"启动托盘图标失败: {e}")
            logger.exception("详细错误信息:")

    def stop(self):
        """停止托盘图标"""
        if self._icon:
            logger.info("正在停止托盘图标...")
            self._icon.stop()
            self._icon = None

    def update_status(self, state: State, face_count: int):
        """更新托盘图标状态

        Args:
            state: 当前状态
            face_count: 检测到的人脸数量
        """
        self._current_state = state
        self._face_count = face_count

        if self._icon:
            # 更新图标
            icon_image = self._create_icon_image(state)
            self._icon.icon = icon_image

            # 更新标题
            status_text = self._get_status_text(state, face_count)
            self._icon.title = f"Touch Fish Guard - {status_text}"

    def _create_icon_image(self, state: State) -> Image.Image:
        """创建图标图像

        Args:
            state: 当前状态

        Returns:
            图标图像
        """
        # 根据状态选择颜色
        color_map = {
            State.MONITORING: (0, 200, 0),      # 绿色
            State.SWITCHED: (255, 200, 0),      # 黄色
            State.PAUSED: (128, 128, 128),      # 灰色
            State.ERROR: (255, 0, 0)            # 红色
        }

        color = color_map.get(state, (128, 128, 128))

        # 创建简单的圆形图标
        size = 64
        image = Image.new('RGB', (size, size), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # 绘制圆形
        margin = 8
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=color,
            outline=(0, 0, 0),
            width=2
        )

        return image

    def _get_status_text(self, state: State, face_count: int) -> str:
        """获取状态文本

        Args:
            state: 当前状态
            face_count: 人脸数量

        Returns:
            状态文本
        """
        state_names = {
            State.MONITORING: "监控中",
            State.SWITCHED: "已切换",
            State.PAUSED: "已暂停",
            State.ERROR: "错误"
        }

        state_name = state_names.get(state, "未知")
        return f"{state_name} ({face_count}人)"

    def _show_status(self, icon, item):
        """显示状态（占位）"""
        pass

    def _toggle_pause(self, icon, item):
        """切换暂停/恢复"""
        try:
            if self._controller.state_manager.is_paused():
                self._controller.resume()
                logger.info("用户恢复监控")
            else:
                self._controller.pause()
                logger.info("用户暂停监控")
        except Exception as e:
            logger.error(f"切换暂停状态失败: {e}")

    def _open_config(self, icon, item):
        """打开配置文件"""
        try:
            config_path = os.path.abspath(self._controller.config_path)
            logger.info(f"打开配置文件: {config_path}")

            # 根据平台使用不同的命令
            if sys.platform == "darwin":
                os.system(f'open "{config_path}"')
            elif sys.platform == "win32":
                os.system(f'start "" "{config_path}"')
            else:
                os.system(f'xdg-open "{config_path}"')

        except Exception as e:
            logger.error(f"打开配置文件失败: {e}")

    def _reload_config(self, icon, item):
        """重新加载配置"""
        try:
            logger.info("用户请求重新加载配置")
            self._controller.reload_config()
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")

    def _show_about(self, icon, item):
        """显示关于信息"""
        logger.info("Touch Fish Guard v1.0 - 摸鱼守护者")

    def _quit(self, icon, item):
        """退出应用"""
        logger.info("用户请求退出应用")
        self._controller.shutdown()
