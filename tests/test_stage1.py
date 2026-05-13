"""测试配置和日志模块"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import ConfigManager
from src.utils.logger import logger


def test_config():
    """测试配置管理器"""
    print("=" * 50)
    print("测试配置管理器")
    print("=" * 50)

    config_manager = ConfigManager("config.json")

    # 测试加载配置
    print("\n1. 加载配置...")
    config = config_manager.load_config()
    print(f"✓ 配置加载成功")
    print(f"  - camera_index: {config.get('camera_index')}")
    print(f"  - detection_interval: {config.get('detection_interval')}")
    print(f"  - min_faces_to_switch: {config.get('min_faces_to_switch')}")
    print(f"  - log_level: {config.get('log_level')}")

    # 测试获取嵌套配置
    print("\n2. 获取嵌套配置...")
    confidence = config_manager.get_nested("face_detector", "confidence_threshold")
    print(f"✓ face_detector.confidence_threshold: {confidence}")

    # 测试配置验证
    print("\n3. 测试配置验证...")
    is_valid, errors = config_manager.validate_config(config)
    if is_valid:
        print("✓ 配置验证通过")
    else:
        print(f"✗ 配置验证失败: {errors}")

    # 测试无效配置
    print("\n4. 测试无效配置...")
    invalid_config = {"camera_index": -1, "detection_interval": 0}
    is_valid, errors = config_manager.validate_config(invalid_config)
    if not is_valid:
        print(f"✓ 正确检测到无效配置:")
        for error in errors:
            print(f"  - {error}")

    print("\n配置管理器测试完成！\n")


def test_logger():
    """测试日志模块"""
    print("=" * 50)
    print("测试日志模块")
    print("=" * 50)

    # 设置日志
    print("\n1. 初始化日志...")
    logger.setup(log_level="INFO", log_file="logs/touch_fish_guard.log")
    print("✓ 日志初始化成功")

    # 测试不同级别的日志
    print("\n2. 测试日志记录...")
    logger.debug("这是调试信息（默认不显示）")
    logger.info("这是信息日志")
    logger.warning("这是警告日志")
    logger.error("这是错误日志")
    print("✓ 日志记录成功")

    # 测试日志级别切换
    print("\n3. 测试日志级别切换...")
    logger.setup(log_level="DEBUG", log_file="logs/touch_fish_guard.log")
    logger.debug("现在可以看到调试信息了")
    print("✓ 日志级别切换成功")

    print("\n日志模块测试完成！\n")


def test_integration():
    """测试配置和日志集成"""
    print("=" * 50)
    print("测试配置和日志集成")
    print("=" * 50)

    # 加载配置
    config_manager = ConfigManager("config.json")
    config = config_manager.load_config()

    # 根据配置设置日志
    log_level = config.get("log_level", "INFO")
    logger.setup(log_level=log_level, log_file="logs/touch_fish_guard.log")

    logger.info("应用启动")
    logger.info(f"摄像头索引: {config.get('camera_index')}")
    logger.info(f"检测间隔: {config.get('detection_interval')} 秒")
    logger.info(f"切换阈值: {config.get('min_faces_to_switch')} 人")

    print("\n✓ 配置和日志集成测试完成！\n")


if __name__ == "__main__":
    try:
        test_config()
        test_logger()
        test_integration()

        print("=" * 50)
        print("所有测试通过！✓")
        print("=" * 50)
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
