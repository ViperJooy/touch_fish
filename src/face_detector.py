"""人脸检测器"""
import os
import sys
import numpy as np
from typing import Optional
from src.utils.logger import logger

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("ONNX Runtime 不可用")


class FaceDetector:
    """人脸检测器（使用 ONNX 模型）"""

    def __init__(self, config: dict):
        """初始化人脸检测器

        Args:
            config: 配置字典
        """
        self._config = config
        self._session: Optional[ort.InferenceSession] = None
        self._confidence_threshold = config.get("face_detector", {}).get("confidence_threshold", 0.7)
        self._nms_threshold = config.get("face_detector", {}).get("nms_threshold", 0.3)

        # 加载模型
        model_path = self._get_model_path(config)
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            logger.error(f"模型文件不存在: {model_path}")
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

    def _get_model_path(self, config: dict) -> str:
        """获取模型路径

        Args:
            config: 配置字典

        Returns:
            模型路径
        """
        model_path = config.get("face_detector", {}).get("model_path", "models/ultra_light_face_detector.onnx")

        # 处理打包后的资源路径
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, model_path)

        return model_path

    def load_model(self, model_path: str) -> None:
        """加载 ONNX 模型

        Args:
            model_path: 模型文件路径
        """
        if not ONNX_AVAILABLE:
            logger.error("ONNX Runtime 不可用，无法加载模型")
            raise ImportError("ONNX Runtime 不可用")

        try:
            logger.info(f"正在加载模型: {model_path}")
            self._session = ort.InferenceSession(model_path)

            # 打印模型信息
            input_name = self._session.get_inputs()[0].name
            input_shape = self._session.get_inputs()[0].shape
            logger.info(f"模型加载成功 - 输入: {input_name}, 形状: {input_shape}")

        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            raise

    def detect_faces(self, frame) -> int:
        """检测人脸

        Args:
            frame: 图像帧 (BGR 格式)

        Returns:
            检测到的人脸数量
        """
        if self._session is None:
            logger.warning("模型未加载")
            return 0

        try:
            # 预处理图像
            input_blob = self._preprocess(frame)

            # 推理
            input_name = self._session.get_inputs()[0].name
            outputs = self._session.run(None, {input_name: input_blob})

            # 后处理
            boxes, scores = self._postprocess(outputs, frame.shape)

            # NMS
            keep_indices = self._nms(boxes, scores, self._nms_threshold)

            face_count = len(keep_indices)

            return face_count

        except Exception as e:
            logger.error(f"人脸检测失败: {e}")
            return 0

    def _preprocess(self, frame):
        """预处理图像

        Args:
            frame: 原始图像帧

        Returns:
            预处理后的输入张量
        """
        import cv2

        # Resize 到模型输入尺寸 (通常是 320x240 或 640x480)
        input_size = (320, 240)
        resized = cv2.resize(frame, input_size)

        # 转换为 RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # 归一化到 [0, 1]
        normalized = rgb.astype(np.float32) / 255.0

        # 转换为 CHW 格式
        transposed = np.transpose(normalized, (2, 0, 1))

        # 添加 batch 维度
        input_blob = np.expand_dims(transposed, axis=0)

        return input_blob

    def _postprocess(self, outputs, original_shape):
        """后处理模型输出

        Args:
            outputs: 模型输出
            original_shape: 原始图像形状

        Returns:
            (boxes, scores) - 检测框和置信度
        """
        # Ultra Light Face Detector 输出格式:
        # outputs[0]: scores [1, 4420, 2] - [background, face]
        # outputs[1]: boxes [1, 4420, 4] - [x1, y1, x2, y2]

        boxes = []
        scores = []

        if len(outputs) >= 2:
            raw_scores = outputs[0][0]  # [4420, 2]
            raw_boxes = outputs[1][0]   # [4420, 4]

            # 提取人脸类别的置信度（索引 1）
            confidences = raw_scores[:, 1]

            # 过滤低置信度的检测
            for i, conf in enumerate(confidences):
                if conf >= self._confidence_threshold:
                    boxes.append(raw_boxes[i])
                    scores.append(conf)

        return np.array(boxes), np.array(scores)

    def _nms(self, boxes, scores, threshold):
        """非极大值抑制

        Args:
            boxes: 检测框数组
            scores: 置信度数组
            threshold: NMS 阈值

        Returns:
            保留的索引列表
        """
        if len(boxes) == 0:
            return []

        # 按置信度排序
        indices = np.argsort(scores)[::-1]

        keep = []
        while len(indices) > 0:
            current = indices[0]
            keep.append(current)

            if len(indices) == 1:
                break

            # 计算 IoU
            ious = self._compute_iou(boxes[current], boxes[indices[1:]])

            # 保留 IoU 小于阈值的框
            indices = indices[1:][ious < threshold]

        return keep

    def _compute_iou(self, box, boxes):
        """计算 IoU

        Args:
            box: 单个检测框 [x1, y1, x2, y2]
            boxes: 多个检测框 [N, 4]

        Returns:
            IoU 数组
        """
        if len(boxes) == 0:
            return np.array([])

        # 计算交集区域
        x1 = np.maximum(box[0], boxes[:, 0])
        y1 = np.maximum(box[1], boxes[:, 1])
        x2 = np.minimum(box[2], boxes[:, 2])
        y2 = np.minimum(box[3], boxes[:, 3])

        # 交集面积
        intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)

        # 各自的面积
        box_area = (box[2] - box[0]) * (box[3] - box[1])
        boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])

        # 并集面积
        union = box_area + boxes_area - intersection

        # IoU
        iou = intersection / (union + 1e-6)

        return iou
