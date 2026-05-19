"""状态管理模块"""
import time
from typing import Optional, Any
from enum import Enum


class State(Enum):
    """应用状态枚举"""
    MONITORING = "MONITORING"  # 监控中
    SWITCHED = "SWITCHED"      # 已切换到目标应用
    PAUSED = "PAUSED"          # 已暂停
    ERROR = "ERROR"            # 错误状态


class StateManager:
    """状态管理器"""

    def __init__(self, config: dict):
        """初始化状态管理器

        Args:
            config: 配置字典
        """
        self._state = State.MONITORING
        self._previous_window: Optional[Any] = None
        self._switch_time: float = 0.0
        self._switch_back_confirm_count_current: int = 0
        self._switch_out_confirm_count_current: int = 0

        # 从配置读取参数
        self._switch_back_delay = config.get("switch_back_delay", 2.0)
        self._switch_back_confirm_count = config.get("switch_back_confirm_count", 3)
        self._switch_out_confirm_count = config.get("switch_out_confirm_count", 3)
        self._switch_back_cooldown = config.get("switch_back_cooldown", 5.0)
        self._last_switch_back_time: float = 0.0

    def get_state(self) -> State:
        """获取当前状态

        Returns:
            当前状态
        """
        return self._state

    def set_state(self, state: State) -> None:
        """设置状态

        Args:
            state: 新状态
        """
        old_state = self._state
        self._state = state

        # 状态切换时的清理工作
        if old_state == State.SWITCHED and state == State.MONITORING:
            # 从 SWITCHED 回到 MONITORING 时重置切换追踪
            self._last_switch_back_time = time.time()
            self.reset_switch_tracking()

    def record_previous_window(self, window: Any) -> None:
        """记录切换前的窗口

        Args:
            window: 窗口对象
        """
        self._previous_window = window

    def get_previous_window(self) -> Optional[Any]:
        """获取切换前的窗口

        Returns:
            窗口对象或 None
        """
        return self._previous_window

    def record_switch_time(self) -> None:
        """记录切换时间"""
        self._switch_time = time.time()

    def can_switch_back(self, now: Optional[float] = None) -> bool:
        """检查是否可以切回原窗口

        Args:
            now: 当前时间戳，如果为 None 则使用当前时间

        Returns:
            是否可以切回
        """
        if now is None:
            now = time.time()

        # 必须在 SWITCHED 状态
        if self._state != State.SWITCHED:
            return False

        # 必须超过延迟时间
        if now - self._switch_time < self._switch_back_delay:
            return False

        # 必须达到确认次数
        if self._switch_back_confirm_count_current < self._switch_back_confirm_count:
            return False

        return True

    def update_switch_back_confirmation(self, face_count: int) -> bool:
        """更新切回确认计数

        Args:
            face_count: 当前检测到的人脸数量

        Returns:
            是否达到切回条件
        """
        # 只在 SWITCHED 状态下更新
        if self._state != State.SWITCHED:
            return False

        # 仅1人（用户回到座位）时计数，准备切回
        # 0人（无人看守）或2人以上（有人靠近）时不切回
        if face_count == 1:
            self._switch_back_confirm_count_current += 1
        else:
            self._switch_back_confirm_count_current = 0
            return False

        # 检查是否达到切回条件
        return self.can_switch_back()

    def reset_switch_tracking(self) -> None:
        """重置切换追踪信息"""
        self._switch_time = 0.0
        self._switch_back_confirm_count_current = 0
        self._switch_out_confirm_count_current = 0
        self._previous_window = None

    def is_in_switch_back_cooldown(self, now: Optional[float] = None) -> bool:
        """检查是否在切回保护期内

        刚切回原窗口后的一段时间内，不触发切换出去，防止振荡。

        Args:
            now: 当前时间戳

        Returns:
            是否在保护期内
        """
        if now is None:
            now = time.time()
        return (now - self._last_switch_back_time) < self._switch_back_cooldown

    def update_switch_out_confirmation(self, face_count: int, min_faces: int) -> bool:
        """更新切换出去的确认计数

        连续多帧检测到多人脸才真正切换，避免误触发。

        Args:
            face_count: 当前检测到的人脸数量
            min_faces: 触发切换的最小人脸数

        Returns:
            是否达到切换条件
        """
        if self._state != State.MONITORING:
            return False

        # 不满足人脸数，重置计数
        if face_count < min_faces:
            self._switch_out_confirm_count_current = 0
            return False

        # 满足人脸数，累加确认
        self._switch_out_confirm_count_current += 1
        return self._switch_out_confirm_count_current >= self._switch_out_confirm_count

    def get_switch_out_progress(self) -> tuple[int, int]:
        """获取切换出去的确认进度

        Returns:
            (当前确认次数, 需要确认次数)
        """
        return (self._switch_out_confirm_count_current, self._switch_out_confirm_count)

    def is_monitoring(self) -> bool:
        """是否处于监控状态"""
        return self._state == State.MONITORING

    def is_switched(self) -> bool:
        """是否处于已切换状态"""
        return self._state == State.SWITCHED

    def is_paused(self) -> bool:
        """是否处于暂停状态"""
        return self._state == State.PAUSED

    def is_error(self) -> bool:
        """是否处于错误状态"""
        return self._state == State.ERROR

    def pause(self) -> None:
        """暂停监控"""
        if self._state in [State.MONITORING, State.SWITCHED]:
            self._state = State.PAUSED

    def resume(self) -> None:
        """恢复监控"""
        if self._state == State.PAUSED:
            self._state = State.MONITORING
            self.reset_switch_tracking()

    def enter_error(self) -> None:
        """进入错误状态"""
        self._state = State.ERROR

    def recover_from_error(self) -> None:
        """从错误状态恢复"""
        if self._state == State.ERROR:
            self._state = State.MONITORING
            self.reset_switch_tracking()

    def get_state_name(self) -> str:
        """获取状态名称（中文）

        Returns:
            状态名称
        """
        state_names = {
            State.MONITORING: "监控中",
            State.SWITCHED: "已切换",
            State.PAUSED: "已暂停",
            State.ERROR: "错误"
        }
        return state_names.get(self._state, "未知")

    def get_switch_back_progress(self) -> tuple[int, int]:
        """获取切回进度

        Returns:
            (当前确认次数, 需要确认次数)
        """
        return (self._switch_back_confirm_count_current, self._switch_back_confirm_count)
