"""测试状态管理器"""
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.state_manager import StateManager, State


def test_state_transitions():
    """测试状态转换"""
    print("=" * 50)
    print("测试状态转换")
    print("=" * 50)

    config = {
        "switch_back_delay": 1.0,
        "switch_back_confirm_count": 3
    }
    state_manager = StateManager(config)

    # 初始状态应该是 MONITORING
    print("\n1. 测试初始状态...")
    assert state_manager.get_state() == State.MONITORING
    assert state_manager.is_monitoring()
    print(f"✓ 初始状态: {state_manager.get_state_name()}")

    # 切换到 SWITCHED
    print("\n2. 测试切换到 SWITCHED...")
    state_manager.set_state(State.SWITCHED)
    state_manager.record_switch_time()
    assert state_manager.get_state() == State.SWITCHED
    assert state_manager.is_switched()
    print(f"✓ 当前状态: {state_manager.get_state_name()}")

    # 切换到 PAUSED
    print("\n3. 测试暂停...")
    state_manager.pause()
    assert state_manager.get_state() == State.PAUSED
    assert state_manager.is_paused()
    print(f"✓ 当前状态: {state_manager.get_state_name()}")

    # 恢复
    print("\n4. 测试恢复...")
    state_manager.resume()
    assert state_manager.get_state() == State.MONITORING
    assert state_manager.is_monitoring()
    print(f"✓ 当前状态: {state_manager.get_state_name()}")

    # 错误状态
    print("\n5. 测试错误状态...")
    state_manager.enter_error()
    assert state_manager.get_state() == State.ERROR
    assert state_manager.is_error()
    print(f"✓ 当前状态: {state_manager.get_state_name()}")

    # 从错误恢复
    print("\n6. 测试从错误恢复...")
    state_manager.recover_from_error()
    assert state_manager.get_state() == State.MONITORING
    print(f"✓ 当前状态: {state_manager.get_state_name()}")

    print("\n状态转换测试完成！\n")


def test_switch_back_delay():
    """测试切回延迟"""
    print("=" * 50)
    print("测试切回延迟")
    print("=" * 50)

    config = {
        "switch_back_delay": 0.5,  # 0.5 秒延迟
        "switch_back_confirm_count": 1
    }
    state_manager = StateManager(config)

    # 切换到 SWITCHED
    print("\n1. 切换到 SWITCHED 状态...")
    state_manager.set_state(State.SWITCHED)
    state_manager.record_switch_time()
    start_time = time.time()
    print("✓ 已切换并记录时间")

    # 立即检查，应该不能切回
    print("\n2. 立即检查是否可以切回...")
    state_manager.update_switch_back_confirmation(1)
    assert not state_manager.can_switch_back(start_time)
    print("✓ 延迟时间未到，不能切回")

    # 等待延迟时间后检查
    print("\n3. 等待延迟时间后检查...")
    time.sleep(0.6)
    now = time.time()
    state_manager.update_switch_back_confirmation(1)
    assert state_manager.can_switch_back(now)
    print("✓ 延迟时间已到，可以切回")

    print("\n切回延迟测试完成！\n")


def test_confirmation_count():
    """测试连续确认次数"""
    print("=" * 50)
    print("测试连续确认次数")
    print("=" * 50)

    config = {
        "switch_back_delay": 0.1,
        "switch_back_confirm_count": 3
    }
    state_manager = StateManager(config)

    # 切换到 SWITCHED
    print("\n1. 切换到 SWITCHED 状态...")
    state_manager.set_state(State.SWITCHED)
    state_manager.record_switch_time()
    time.sleep(0.2)  # 等待延迟时间
    print("✓ 已切换")

    # 第一次确认
    print("\n2. 第一次检测到 1 人...")
    result = state_manager.update_switch_back_confirmation(1)
    progress = state_manager.get_switch_back_progress()
    print(f"  确认进度: {progress[0]}/{progress[1]}")
    assert not result
    assert progress[0] == 1
    print("✓ 未达到切回条件")

    # 第二次确认
    print("\n3. 第二次检测到 1 人...")
    result = state_manager.update_switch_back_confirmation(1)
    progress = state_manager.get_switch_back_progress()
    print(f"  确认进度: {progress[0]}/{progress[1]}")
    assert not result
    assert progress[0] == 2
    print("✓ 未达到切回条件")

    # 第三次确认
    print("\n4. 第三次检测到 1 人...")
    result = state_manager.update_switch_back_confirmation(1)
    progress = state_manager.get_switch_back_progress()
    print(f"  确认进度: {progress[0]}/{progress[1]}")
    assert result
    assert progress[0] == 3
    print("✓ 达到切回条件")

    print("\n连续确认次数测试完成！\n")


def test_confirmation_reset():
    """测试确认计数重置"""
    print("=" * 50)
    print("测试确认计数重置")
    print("=" * 50)

    config = {
        "switch_back_delay": 0.1,
        "switch_back_confirm_count": 3
    }
    state_manager = StateManager(config)

    # 切换到 SWITCHED
    print("\n1. 切换到 SWITCHED 状态...")
    state_manager.set_state(State.SWITCHED)
    state_manager.record_switch_time()
    time.sleep(0.2)
    print("✓ 已切换")

    # 两次确认
    print("\n2. 两次检测到 1 人...")
    state_manager.update_switch_back_confirmation(1)
    state_manager.update_switch_back_confirmation(1)
    progress = state_manager.get_switch_back_progress()
    print(f"  确认进度: {progress[0]}/{progress[1]}")
    assert progress[0] == 2

    # 检测到多人，应该重置计数
    print("\n3. 检测到 2 人...")
    result = state_manager.update_switch_back_confirmation(2)
    progress = state_manager.get_switch_back_progress()
    print(f"  确认进度: {progress[0]}/{progress[1]}")
    assert not result
    assert progress[0] == 0
    print("✓ 确认计数已重置")

    print("\n确认计数重置测试完成！\n")


def test_paused_state():
    """测试暂停状态"""
    print("=" * 50)
    print("测试暂停状态")
    print("=" * 50)

    config = {
        "switch_back_delay": 0.1,
        "switch_back_confirm_count": 1
    }
    state_manager = StateManager(config)

    # 暂停
    print("\n1. 暂停监控...")
    state_manager.pause()
    assert state_manager.is_paused()
    print(f"✓ 当前状态: {state_manager.get_state_name()}")

    # 在暂停状态下更新确认，应该返回 False
    print("\n2. 在暂停状态下尝试更新确认...")
    result = state_manager.update_switch_back_confirmation(1)
    assert not result
    print("✓ 暂停状态不处理确认")

    # 在暂停状态下不能切回
    print("\n3. 在暂停状态下检查是否可以切回...")
    assert not state_manager.can_switch_back()
    print("✓ 暂停状态不能切回")

    print("\n暂停状态测试完成！\n")


def test_window_tracking():
    """测试窗口追踪"""
    print("=" * 50)
    print("测试窗口追踪")
    print("=" * 50)

    config = {
        "switch_back_delay": 1.0,
        "switch_back_confirm_count": 3
    }
    state_manager = StateManager(config)

    # 记录窗口
    print("\n1. 记录前一个窗口...")
    mock_window = {"title": "Chrome", "id": 12345}
    state_manager.record_previous_window(mock_window)
    assert state_manager.get_previous_window() == mock_window
    print(f"✓ 已记录窗口: {mock_window}")

    # 重置后窗口应该被清除
    print("\n2. 重置切换追踪...")
    state_manager.reset_switch_tracking()
    assert state_manager.get_previous_window() is None
    print("✓ 窗口记录已清除")

    print("\n窗口追踪测试完成！\n")


if __name__ == "__main__":
    try:
        test_state_transitions()
        test_switch_back_delay()
        test_confirmation_count()
        test_confirmation_reset()
        test_paused_state()
        test_window_tracking()

        print("=" * 50)
        print("所有测试通过！✓")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
