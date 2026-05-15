"""配置管理模块"""
import json
import os
from typing import Tuple, List, Dict, Any


class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG = {
        "target_app": "Visual Studio Code",
        "camera_index": 0,
        "detection_interval": 0.5,
        "min_faces_to_switch": 2,
        "switch_back_delay": 2.0,
        "switch_back_confirm_count": 3,
        "face_detector": {
            "backend": "ultra_light_onnx",
            "model_path": "models/ultra_light_face_detector.onnx",
            "confidence_threshold": 0.7,
            "nms_threshold": 0.3
        },
        "auto_start": False,
        "log_level": "INFO"
    }

    def __init__(self, config_path: str = "config.json"):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件

        Returns:
            配置字典
        """
        if not os.path.exists(self.config_path):
            self.save_default_config()
            self._config = self.DEFAULT_CONFIG.copy()
            return self._config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            # 验证配置
            is_valid, errors = self.validate_config(loaded_config)
            if not is_valid:
                print(f"配置验证失败: {errors}")
                print("使用默认配置")
                self._config = self.DEFAULT_CONFIG.copy()
            else:
                # 合并默认配置，确保所有字段都存在
                self._config = self._merge_with_defaults(loaded_config)

            return self._config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            print("使用默认配置")
            self._config = self.DEFAULT_CONFIG.copy()
            return self._config

    def reload_config(self) -> Dict[str, Any]:
        """重新加载配置文件

        Returns:
            配置字典
        """
        return self.load_config()

    def save_default_config(self) -> None:
        """保存默认配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            print(f"已生成默认配置文件: {self.config_path}")
        except Exception as e:
            print(f"保存默认配置失败: {e}")

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证配置

        Args:
            config: 配置字典

        Returns:
            (是否有效, 错误列表)
        """
        errors = []

        # 验证必需字段
        required_fields = [
            "camera_index",
            "detection_interval",
            "min_faces_to_switch",
            "switch_back_delay",
            "switch_back_confirm_count",
            "log_level"
        ]

        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")

        # 验证数值范围
        if "camera_index" in config:
            if not isinstance(config["camera_index"], int) or config["camera_index"] < 0:
                errors.append("camera_index 必须是非负整数")

        if "detection_interval" in config:
            if not isinstance(config["detection_interval"], (int, float)) or config["detection_interval"] <= 0:
                errors.append("detection_interval 必须是正数")

        if "min_faces_to_switch" in config:
            if not isinstance(config["min_faces_to_switch"], int) or config["min_faces_to_switch"] < 2:
                errors.append("min_faces_to_switch 必须是大于等于 2 的整数")

        if "switch_back_delay" in config:
            if not isinstance(config["switch_back_delay"], (int, float)) or config["switch_back_delay"] < 0:
                errors.append("switch_back_delay 必须是非负数")

        if "switch_back_confirm_count" in config:
            if not isinstance(config["switch_back_confirm_count"], int) or config["switch_back_confirm_count"] < 1:
                errors.append("switch_back_confirm_count 必须是正整数")

        if "log_level" in config:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config["log_level"] not in valid_levels:
                errors.append(f"log_level 必须是以下之一: {valid_levels}")

        # 验证 face_detector 配置
        if "face_detector" in config:
            fd_config = config["face_detector"]
            if not isinstance(fd_config, dict):
                errors.append("face_detector 必须是字典")
            else:
                if "confidence_threshold" in fd_config:
                    if not isinstance(fd_config["confidence_threshold"], (int, float)) or \
                       not (0 <= fd_config["confidence_threshold"] <= 1):
                        errors.append("confidence_threshold 必须在 0-1 之间")

                if "nms_threshold" in fd_config:
                    if not isinstance(fd_config["nms_threshold"], (int, float)) or \
                       not (0 <= fd_config["nms_threshold"] <= 1):
                        errors.append("nms_threshold 必须在 0-1 之间")

        return len(errors) == 0, errors

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """将加载的配置与默认配置合并

        Args:
            config: 加载的配置

        Returns:
            合并后的配置
        """
        merged = self.DEFAULT_CONFIG.copy()

        # 合并顶层字段
        for key, value in config.items():
            if key in merged:
                if isinstance(value, dict) and isinstance(merged[key], dict):
                    # 递归合并字典
                    merged[key] = {**merged[key], **value}
                else:
                    merged[key] = value

        return merged

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self._config.get(key, default)

    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """获取嵌套配置项

        Args:
            keys: 配置键路径
            default: 默认值

        Returns:
            配置值
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default
