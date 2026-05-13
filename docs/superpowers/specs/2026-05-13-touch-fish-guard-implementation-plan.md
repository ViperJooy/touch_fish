# Touch Fish Guard 实施计划

## 目标

基于 `2026-05-13-touch-fish-guard-design.md` 的设计规格，按阶段实现 Touch Fish Guard。实施顺序采用“先跑通最小闭环，再补托盘、跨平台和打包”的策略，降低模型、摄像头、窗口管理和打包同时带来的不确定性。

## 总体实施顺序

1. 创建项目骨架、配置、日志、入口。
2. 实现 `StateManager`，先用测试验证状态切换。
3. 实现 `CameraMonitor`，确认摄像头采集稳定。
4. 实现 `FaceDetector`，接入 ONNX 模型。
5. 实现 `WindowManager`，先做当前平台，再补另一个平台。
6. 在 `MainController` 中串起检测、状态、窗口切换。
7. 接入 `TrayIcon`。
8. 做 PyInstaller 打包和资源路径修正。
9. 做 macOS / Windows 真机验收。

## 阶段 0：项目骨架

目标：建立可运行的 Python 应用结构。

创建文件：

- `requirements.txt`
- `config.json`
- `build.py`
- `src/__init__.py`
- `src/main.py`
- `src/main_controller.py`
- `src/utils/__init__.py`
- `src/utils/config.py`
- `src/utils/logger.py`
- `models/.gitkeep`
- `resources/.gitkeep`

工作内容：

- 创建设计文档中定义的目录结构。
- 写入默认 `config.json`。
- `src/main.py` 只负责启动 `MainController`。
- `MainController` 先只加载配置、初始化日志、进入占位运行流程。

验证方式：

```bash
python -m src.main
```

期望结果：

- 应用能启动。
- 能读取或生成 `config.json`。
- 能写入日志文件。
- 缺模型、缺摄像头时暂时不阻塞骨架验证。

## 阶段 1：配置与日志

目标：把配置和日志作为基础设施先稳定下来。

实现文件：

- `src/utils/config.py`
- `src/utils/logger.py`

`ConfigManager` 建议接口：

```python
class ConfigManager:
    def load_config(self) -> dict: ...
    def reload_config(self) -> dict: ...
    def save_default_config(self) -> None: ...
    def validate_config(self, config: dict) -> tuple[bool, list[str]]: ...
```

默认配置字段：

```json
{
  "vscode_path": "auto",
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
  "auto_start": false,
  "log_level": "INFO"
}
```

日志策略：

- 默认写到 `logs/touch_fish_guard.log`。
- 不弹通知。
- 记录启动、配置加载、摄像头错误、模型错误、窗口切换错误。

验证方式：

- 删除 `config.json` 后启动，确认自动生成。
- 修改 `log_level` 后重载，确认日志级别生效。
- 写入非法字段，确认有日志记录并尽量回退默认值。

## 阶段 2：状态机

目标：先把切换逻辑做成纯状态逻辑，便于测试。

实现文件：

- `src/state_manager.py`

状态：

```text
MONITORING
SWITCHED
PAUSED
ERROR
```

`StateManager` 建议接口：

```python
class StateManager:
    def get_state(self) -> str: ...
    def set_state(self, state: str) -> None: ...
    def record_previous_window(self, window) -> None: ...
    def get_previous_window(self): ...
    def record_switch_time(self) -> None: ...
    def can_switch_back(self, now: float) -> bool: ...
    def update_switch_back_confirmation(self, face_count: int) -> bool: ...
    def reset_switch_tracking(self) -> None: ...
```

核心规则：

- `MONITORING` 下检测到 `face_count >= min_faces_to_switch` 才触发切换。
- 切换后进入 `SWITCHED`。
- `SWITCHED` 状态至少保持 `switch_back_delay` 秒。
- 达到 `switch_back_confirm_count` 次连续检测到 `face_count <= 1` 后，才允许切回。
- `PAUSED` 状态不执行检测决策。
- `ERROR` 状态只允许恢复、重载配置或退出。

验证方式：

- 用单元测试覆盖 `MONITORING -> SWITCHED -> MONITORING`。
- 验证切回延迟。
- 验证连续确认次数。
- 验证暂停状态不触发切换。

## 阶段 3：摄像头采集

目标：先跑通摄像头采帧，不急着接真实模型。

实现文件：

- `src/camera_monitor.py`

`CameraMonitor` 建议接口：

```python
class CameraMonitor:
    def start_monitoring(self) -> None: ...
    def stop_monitoring(self) -> None: ...
    @property
    def is_running(self) -> bool: ...
    @property
    def current_face_count(self) -> int: ...
```

实现要点：

- 使用 `cv2.VideoCapture(camera_index)`。
- 独立线程采集。
- 按 `detection_interval` 控制检测频率。
- 每次采集后调用 `FaceDetector.detect_faces(frame)`。
- 将人脸数量回调给 `MainController`。
- 停止时释放摄像头。

建议先做一个临时 `FakeFaceDetector` 或让 `FaceDetector` 返回 `0`，只验证摄像头循环不阻塞。

验证方式：

- 摄像头能打开。
- 程序能持续采帧。
- 停止时摄像头被释放。
- 摄像头不可用时进入 `ERROR` 状态并写日志。

## 阶段 4：人脸检测

目标：接入 ONNX 模型并返回人脸数量。

实现文件：

- `src/face_detector.py`
- `models/ultra_light_face_detector.onnx`

`FaceDetector` 建议接口：

```python
class FaceDetector:
    def load_model(self, model_path: str) -> None: ...
    def detect_faces(self, frame) -> int: ...
```

实现要点：

- 启动时检查模型文件是否存在。
- 使用 `onnxruntime.InferenceSession` 加载模型。
- 使用 OpenCV 做图像 resize、归一化、通道转换。
- 推理后按 `confidence_threshold` 过滤。
- 对检测框做 NMS，避免重复计数。
- 返回最终人脸数量。

模型处理：

- 模型必须本地放在 `models/ultra_light_face_detector.onnx`。
- 不在运行时下载模型。
- 打包时必须带上 `models/`。
- 如果模型缺失，进入 `ERROR`，不要静默降级到 Haar Cascade。

验证方式：

- 用固定图片验证 `detect_faces(frame)`。
- 单人图片返回 `1`。
- 双人图片返回 `2` 或更多。
- 无人图片返回 `0`。
- 模型缺失时错误可控且有日志。

## 阶段 5：窗口管理抽象

目标：把平台差异限制在 `window_manager/` 内。

实现文件：

- `src/window_manager/__init__.py`
- `src/window_manager/base.py`
- `src/window_manager/macos.py`
- `src/window_manager/windows.py`

抽象接口：

```python
class BaseWindowManager:
    def get_active_window(self): ...
    def find_vscode_window(self): ...
    def activate_window(self, window) -> bool: ...
    def launch_vscode(self) -> bool: ...
    def activate_or_launch_vscode(self) -> bool: ...
```

平台选择：

```python
def create_window_manager(config):
    if platform.system() == "Darwin":
        return MacOSWindowManager(config)
    if platform.system() == "Windows":
        return WindowsWindowManager(config)
    raise UnsupportedPlatformError(...)
```

macOS 实现：

- 使用 `AppKit` 获取运行应用。
- 使用 `Quartz` 或 `NSWorkspace` 获取当前活动应用。
- 激活 VS Code 优先找 bundle/application name。
- 未运行时执行 `open -a "Visual Studio Code"`。

Windows 实现：

- 使用 `pywin32` / `pygetwindow` 枚举窗口。
- 优先查找已运行 VS Code 窗口。
- 未运行时优先使用 `config["vscode_path"]`。
- 再检查常见路径。
- 最后尝试 `code` 命令或失败记录日志。

验证方式：

- VS Code 已运行时能激活。
- VS Code 未运行时能启动。
- 切换前能记录当前窗口。
- 切回时原窗口已关闭不会报崩溃。
- macOS 和 Windows 分别做真机验证。

## 阶段 6：主控制器串联

目标：实现完整状态流。

实现文件：

- `src/main_controller.py`

主流程：

```text
启动
  -> 加载配置
  -> 初始化日志
  -> 初始化 StateManager
  -> 初始化 WindowManager
  -> 初始化 FaceDetector
  -> 初始化 CameraMonitor
  -> 启动监控
```

检测回调逻辑：

```text
如果状态是 PAUSED:
  忽略检测结果

如果 face_count >= min_faces_to_switch 且状态是 MONITORING:
  记录当前活动窗口
  激活或启动 VS Code
  成功后进入 SWITCHED

如果 face_count <= 1 且状态是 SWITCHED:
  检查 switch_back_delay
  检查 switch_back_confirm_count
  满足后激活原窗口
  回到 MONITORING
```

需要注意：

- 检测到多人时要立即切换，不需要连续确认。
- 切回需要延迟和连续确认，避免抖动。
- 切换失败时不要破坏当前窗口状态。
- 原窗口失效时清空记录，回到 `MONITORING`。

验证方式：

- mock `FaceDetector` 输入 `0, 1, 2, 1, 1, 1`。
- 验证状态转换符合预期。
- mock `WindowManager` 验证调用顺序。

## 阶段 7：系统托盘

目标：提供静默后台控制入口。

实现文件：

- `src/tray_icon.py`
- `resources/icon_green.png`
- `resources/icon_yellow.png`
- `resources/icon_gray.png`
- `resources/icon_red.png`

菜单：

```text
Touch Fish Guard
├─ 监控中 / 已暂停
├─ 当前状态: 检测到 N 人
├─ 暂停 / 恢复
├─ 打开配置文件
├─ 重新加载配置
├─ 关于
└─ 退出
```

`TrayIcon` 建议接口：

```python
class TrayIcon:
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def update_status(self, state: str, face_count: int) -> None: ...
```

实现要点：

- `pystray` 通常会阻塞主线程，需要和 `CameraMonitor` 线程配合。
- 菜单项调用 `MainController.pause()`、`resume()`、`reload_config()`、`shutdown()`。
- 图标状态：绿色是 `MONITORING`，黄色是 `SWITCHED`，灰色是 `PAUSED`，红色是 `ERROR`。

验证方式：

- 点击暂停后不再触发窗口切换。
- 点击恢复后继续检测。
- 点击重新加载配置后新阈值生效。
- 点击退出后释放摄像头并关闭托盘。

## 阶段 8：打包

目标：生成 macOS 和 Windows 可运行产物。

实现文件：

- `build.py`

打包命令封装：

macOS：

```bash
pyinstaller --onefile --windowed \
  --add-data "resources:resources" \
  --add-data "models:models" \
  --name "TouchFishGuard" \
  src/main.py
```

Windows：

```bash
pyinstaller --onefile --windowed ^
  --add-data "resources;resources" ^
  --add-data "models;models" ^
  --name "TouchFishGuard" ^
  src/main.py
```

建议 `build.py` 根据平台自动选择 `--add-data` 分隔符。

资源路径必须统一处理：

```python
def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(app_root, relative_path)
```

验证方式：

- 打包后启动无控制台窗口。
- 能找到托盘图标。
- 能找到 ONNX 模型。
- 能读取或生成配置。
- 摄像头检测可用。
- VS Code 切换可用。

## 依赖策略

初版可以先使用一个 `requirements.txt`：

```text
opencv-python
onnxruntime
numpy
pystray
Pillow
pyinstaller
```

后续建议拆分平台依赖。

`requirements-macos.txt`：

```text
pyobjc-framework-Cocoa
pyobjc-framework-Quartz
```

`requirements-windows.txt`：

```text
pywin32
pygetwindow
```

这样可以避免在 macOS 安装 Windows 包或在 Windows 安装 PyObjC 失败。

## 主要风险

### 模型文件来源和格式

需要确认 `ultra_light_face_detector.onnx` 的输入输出张量格式，否则 `FaceDetector` 后处理会卡住。

缓解方式：

- 先手动加载模型并打印输入输出元信息。
- 根据实际模型输出写后处理逻辑。
- 准备固定测试图片做回归验证。

### macOS 权限

摄像头权限和窗口激活权限可能导致功能正常但无法执行切换。

缓解方式：

- 启动时检查摄像头是否可打开。
- 窗口激活失败时写日志并进入可恢复状态。
- 文档中说明需要授予摄像头和辅助功能权限。

### Windows 窗口查找

VS Code 安装路径、窗口标题、多实例都会影响激活逻辑。

缓解方式：

- 优先查找已运行窗口。
- 其次读取 `vscode_path`。
- 再检查常见安装路径。
- 所有失败都记录日志，不破坏当前窗口。

### PyInstaller 资源路径

`--onefile` 下模型和图标路径经常出问题。

缓解方式：

- 统一实现 `resource_path()`。
- 开发态和打包态使用同一套资源定位逻辑。
- 如果 `--onefile` 不稳定，切换为 `--onedir` 发布。

### 误检与漏检

初版应优先避免漏报，可以接受少量误报，再通过阈值和 NMS 调整。

缓解方式：

- 多人时立即切换。
- 切回时使用延迟和连续确认。
- 暴露 `confidence_threshold` 和 `nms_threshold` 到配置文件。

## 第一批落地范围

建议第一批只实现以下内容：

- 项目骨架
- `ConfigManager`
- `Logger`
- `StateManager`
- `MainController` 占位流程

这部分不依赖摄像头、模型、托盘和平台权限，适合作为可验证的最小基础。