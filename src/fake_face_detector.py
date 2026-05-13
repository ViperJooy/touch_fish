"""假的人脸检测器（用于测试）"""
from src.utils.logger import logger


class FakeFaceDetector:
    """假的人脸检测器，用于测试摄像头采集"""

    def __init__(self, config: dict):
        """初始化假检测器

        Args:
            config: 配置字典
        """
        self._detection_count = 0
        logger.info("使用假人脸检测器（测试模式）")

    def detect_faces(self, frame) -> int:
        """检测人脸（总是返回 0）

        Args:
            frame: 图像帧

        Returns:
            人脸数量（固定返回 0）
        """
        self._detection_count += 1

        # 每 10 次检测输出一次日志
        if self._detection_count % 10 == 0:
            logger.debug(f"已执行 {self._detection_count} 次假检测")

        return 0
