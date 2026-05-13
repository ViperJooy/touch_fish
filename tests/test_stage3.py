"""测试摄像头监控模块"""
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.camera_monitor import CameraMonitor
from src.fake_face_detector import FakeFaceDetector
from src.utils.logger import logger


def test_camera_monitor_with_fake_detector():
    """测试摄像头监控（使用假检测器）"""
    print("=" * 50)
    print("测试摄像头监控（使用假检测器）")
    print("=" * 50)

    # 初始化日志
    logger.setup(log_level="INFO")

    # 配置
    config = {
        "camera_index": 0,
        "detection_interval": 0.2,
        "face_detector": {}
    }

    # 创建假检测器
    print("\n1. 创建假人脸检测器...")
    fake_detector = FakeFaceDetector(config)
    print("✓ 假检测器已创建")

    # 检测回调计数器
    detection_count = [0]
    detected_faces = []

    def on_detection(face_count: int):
        detection_count[0] += 1
        detected_faces.append(face_count)
        if detection_count[0] <= 3:
            print(f"  检测回调 #{detection_count[0]}: 检测到 {face_count} 人")

    # 创建摄像头监控器
    print("\n2. 创建摄像头监控器...")
    camera_monitor = CameraMonitor(config, fake_detector, on_detection)
    print("✓ 监控器已创建")

    # 启动监控
    print("\n3. 启动摄像头监控...")
    success = camera_monitor.start_monitoring()

    if not success:
        print("✗ 无法启动摄像头监控（可能没有可用的摄像头）")
        print("  这在 CI 环境或无摄像头的机器上是正常的")
        return False

    print("✓ 监控已启动")
    assert camera_monitor.is_running

    # 获取摄像头信息
    print("\n4. 获取摄像头信息...")
    camera_info = camera_monitor.get_camera_info()
    if camera_info.get("available"):
        print(f"✓ 摄像头信息:")
        print(f"  - 索引: {camera_info.get('index')}")
        print(f"  - 分辨率: {camera_info.get('width')}x{camera_info.get('height')}")
        print(f"  - FPS: {camera_info.get('fps')}")
    else:
        print("✗ 无法获取摄像头信息")

    # 运行一段时间
    print("\n5. 运行监控 1 秒...")
    time.sleep(1.0)
    print(f"✓ 共执行了 {detection_count[0]} 次检测")

    # 检查当前人脸数量
    print("\n6. 检查当前人脸数量...")
    face_count = camera_monitor.current_face_count
    print(f"✓ 当前检测到 {face_count} 人")

    # 停止监控
    print("\n7. 停止监控...")
    camera_monitor.stop_monitoring()
    assert not camera_monitor.is_running
    print("✓ 监控已停止")

    # 验证检测次数合理
    print("\n8. 验证检测次数...")
    expected_min = 3  # 至少应该有几次检测
    if detection_count[0] >= expected_min:
        print(f"✓ 检测次数合理: {detection_count[0]} >= {expected_min}")
    else:
        print(f"✗ 检测次数过少: {detection_count[0]} < {expected_min}")
        return False

    print("\n摄像头监控测试完成！\n")
    return True


def test_camera_monitor_start_stop():
    """测试摄像头监控启动和停止"""
    print("=" * 50)
    print("测试摄像头监控启动和停止")
    print("=" * 50)

    config = {
        "camera_index": 0,
        "detection_interval": 0.5,
    }

    fake_detector = FakeFaceDetector(config)
    camera_monitor = CameraMonitor(config, fake_detector)

    # 测试启动
    print("\n1. 测试启动...")
    success = camera_monitor.start_monitoring()

    if not success:
        print("✗ 无法启动摄像头（可能没有可用的摄像头）")
        return False

    assert camera_monitor.is_running
    print("✓ 启动成功")

    # 测试重复启动
    print("\n2. 测试重复启动...")
    success = camera_monitor.start_monitoring()
    assert success
    assert camera_monitor.is_running
    print("✓ 重复启动被正确处理")

    # 测试停止
    print("\n3. 测试停止...")
    camera_monitor.stop_monitoring()
    assert not camera_monitor.is_running
    print("✓ 停止成功")

    # 测试重复停止
    print("\n4. 测试重复停止...")
    camera_monitor.stop_monitoring()
    assert not camera_monitor.is_running
    print("✓ 重复停止被正确处理")

    print("\n启动停止测试完成！\n")
    return True


if __name__ == "__main__":
    try:
        # 测试 1
        result1 = test_camera_monitor_with_fake_detector()

        # 测试 2
        result2 = test_camera_monitor_start_stop()

        if result1 and result2:
            print("=" * 50)
            print("所有测试通过！✓")
            print("=" * 50)
        else:
            print("=" * 50)
            print("部分测试失败（可能是因为没有可用的摄像头）")
            print("=" * 50)

    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
