"""摄像头监控模块"""
import threading
import time
import cv2
from typing import Optional, Callable
from src.utils.logger import logger


class CameraMonitor:
    """摄像头监控器"""

    def __init__(self, config: dict, face_detector, on_detection_callback: Optional[Callable] = None):
        """初始化摄像头监控器

        Args:
            config: 配置字典
            face_detector: 人脸检测器实例
            on_detection_callback: 检测回调函数，参数为 (face_count: int)
        """
        self._camera_index = config.get("camera_index", 0)
        self._detection_interval = config.get("detection_interval", 0.5)
        self._face_detector = face_detector
        self._on_detection_callback = on_detection_callback

        self._capture: Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_face_count = 0
        self._lock = threading.Lock()

    def start_monitoring(self) -> bool:
        """启动监控

        Returns:
            是否成功启动
        """
        if self._running:
            logger.warning("摄像头监控已在运行")
            return True

        # 尝试打开摄像头
        try:
            self._capture = cv2.VideoCapture(self._camera_index)
            if not self._capture.isOpened():
                logger.error(f"无法打开摄像头 {self._camera_index}")
                return False

            logger.info(f"成功打开摄像头 {self._camera_index}")
        except Exception as e:
            logger.error(f"打开摄像头时出错: {e}")
            return False

        # 启动监控线程
        self._running = True
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()
        logger.info("摄像头监控线程已启动")

        return True

    def stop_monitoring(self) -> None:
        """停止监控"""
        if not self._running:
            return

        logger.info("正在停止摄像头监控...")
        self._running = False

        # 等待线程结束
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        # 释放摄像头
        if self._capture:
            self._capture.release()
            self._capture = None

        logger.info("摄像头监控已停止")

    def _monitoring_loop(self) -> None:
        """监控循环（在独立线程中运行）"""
        logger.info("监控循环开始")

        while self._running:
            try:
                # 读取帧
                ret, frame = self._capture.read()
                if not ret:
                    logger.warning("无法读取摄像头帧")
                    time.sleep(self._detection_interval)
                    continue

                # 人脸检测
                face_count = self._face_detector.detect_faces(frame)

                # 更新当前人脸数量
                with self._lock:
                    self._current_face_count = face_count

                # 调用回调
                if self._on_detection_callback:
                    try:
                        self._on_detection_callback(face_count)
                    except Exception as e:
                        logger.error(f"检测回调执行出错: {e}")

                # 等待下一次检测
                time.sleep(self._detection_interval)

            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(self._detection_interval)

        logger.info("监控循环结束")

    @property
    def is_running(self) -> bool:
        """是否正在运行

        Returns:
            是否正在运行
        """
        return self._running

    @property
    def current_face_count(self) -> int:
        """当前检测到的人脸数量

        Returns:
            人脸数量
        """
        with self._lock:
            return self._current_face_count

    def get_camera_info(self) -> dict:
        """获取摄像头信息

        Returns:
            摄像头信息字典
        """
        if not self._capture or not self._capture.isOpened():
            return {"available": False}

        try:
            width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self._capture.get(cv2.CAP_PROP_FPS))

            return {
                "available": True,
                "index": self._camera_index,
                "width": width,
                "height": height,
                "fps": fps
            }
        except Exception as e:
            logger.error(f"获取摄像头信息出错: {e}")
            return {"available": False, "error": str(e)}
