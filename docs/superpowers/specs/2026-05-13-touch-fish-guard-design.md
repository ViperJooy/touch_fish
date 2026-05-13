# Touch Fish Guard 设计规格

## 背景

Touch Fish Guard 是一个跨平台桌面后台工具。它通过电脑摄像头检测画面中是否出现 2 个及以上人脸；当满足条件时，立即将当前活动窗口切换到 VS Code；当画面恢复为 1 人或 0 人时，自动切回之前的窗口。

目标使用场景是：用户当前可能在看视频或浏览非工作内容，当摄像头画面中出现其他人时，工具自动切换到工作界面，且整个过程静默运行。

## 需求

### 功能需求

- 支持 macOS 和 Windows。
- 通过摄像头持续检测画面中的人脸数量。
- 检测到 2 个及以上人脸时，立即切换到 VS Code。
- 如果 VS Code 已运行，激活现有 VS Code 窗口。
- 如果 VS Code 未运行，自动启动 VS Code。
- 当检测恢复为 1 人或 0 人时，自动切回切换前的窗口。
- 使用系统托盘图标作为主要控制入口。
- 默认静默运行，不显示系统通知。
- 支持暂停、恢复、退出、打开配置文件、重新加载配置。

### 非功能需求

- 人脸检测必须在本地完成，不调用云端 API。
- 检测方案要轻量，适合后台常驻。
- 窗口切换要尽量快，优先避免漏报。
- 配置可通过本地 `config.json` 调整。
- 需要日志文件用于排查问题，但不主动弹通知。

## 技术方案

采用 Python + OpenCV + ONNX Runtime + pystray 的方案。

- Python 负责应用主逻辑和跨平台集成。
- OpenCV 负责摄像头采集和图像预处理。
- Ultra-Light-Fast-Generic-Face-Detector 负责轻量级人脸检测。
- ONNX Runtime 负责加载和执行人脸检测模型。
- pystray 负责系统托盘图标和菜单。
- macOS 使用 PyObjC/AppKit 实现应用激活和窗口切换。
- Windows 使用 pywin32/pygetwindow 实现窗口查找和切换。

Ultra-Light-Fast-Generic-Face-Detector 替代 OpenCV Haar Cascade 作为默认检测器。原因是它仍然轻量，但比 Haar Cascade 对角度、光照和部分遮挡更稳健。模型文件会随项目放在 `models/` 目录中；实现阶段优先使用该项目导出的 ONNX 模型，避免运行时依赖外部仓库或网络。

## 架构

核心模块如下：

- `MainController`：应用入口，协调托盘、摄像头、人脸检测、窗口管理和状态管理。
- `CameraMonitor`：管理摄像头采集循环。
- `FaceDetector`：封装 Ultra-Light 人脸检测模型。
- `WindowManager`：跨平台窗口管理抽象。
- `StateManager`：维护当前监控状态、切换状态和原窗口信息。
- `TrayIcon`：系统托盘图标、菜单和状态展示。
- `ConfigManager`：读取、生成和重新加载配置。
- `Logger`：应用日志。

## 工作流

```text
启动应用
  -> 加载配置
  -> 初始化日志
  -> 初始化窗口管理器
  -> 初始化托盘图标
  -> 初始化摄像头和人脸检测器
  -> 进入监控循环

监控循环:
  -> 每 0.5 秒采集一帧
  -> FaceDetector 检测人脸数量
  -> 如果人脸数量 >= 2 且当前未切换:
       记录当前活动窗口
       激活或启动 VS Code
       状态改为 SWITCHED
  -> 如果人脸数量 <= 1 且当前已切换:
       等待最小保持时间
       连续确认若干次后切回原窗口
       状态改为 MONITORING
```

## 模块设计

### CameraMonitor

职责：

- 打开指定摄像头。
- 在独立线程中执行采集循环。
- 将采集到的帧交给 `FaceDetector`。
- 将检测结果交给 `MainController` 做状态决策。
- 停止时释放摄像头资源。

关键接口：

- `start_monitoring()`
- `stop_monitoring()`
- `is_running`
- `current_face_count`

### FaceDetector

职责：

- 加载 Ultra-Light-Fast-Generic-Face-Detector 模型。
- 对摄像头帧进行预处理。
- 执行 ONNX Runtime 推理。
- 后处理检测框和置信度。
- 返回画面中的人脸数量。

实现策略：

- 默认使用 1MB 轻量模型。
- 默认输入尺寸使用模型推荐尺寸。
- 低于置信度阈值的检测结果会被过滤。
- 对重叠检测框执行 NMS，避免同一张脸重复计数。

关键接口：

- `detect_faces(frame) -> int`
- `load_model(model_path)`

### WindowManager

职责：

- 获取当前活动窗口。
- 查找正在运行的 VS Code。
- 激活 VS Code 窗口。
- VS Code 未运行时启动 VS Code。
- 切回之前记录的窗口。

平台实现：

- `window_manager/base.py` 定义抽象接口。
- `window_manager/macos.py` 使用 AppKit、Quartz 和 `open -a "Visual Studio Code"`。
- `window_manager/windows.py` 使用 pywin32、pygetwindow 和常见 VS Code 安装路径。

关键接口：

- `get_active_window()`
- `find_vscode_window()`
- `activate_window(window)`
- `launch_vscode()`
- `activate_or_launch_vscode()`

### StateManager

状态：

- `MONITORING`：正常监控中。
- `SWITCHED`：已自动切换到 VS Code。
- `PAUSED`：用户手动暂停。
- `ERROR`：摄像头、权限或模型加载失败。

职责：

- 记录切换前窗口。
- 记录切换时间。
- 防止频繁切换抖动。
- 管理是否允许切回原窗口。

### TrayIcon

菜单：

```text
Touch Fish Guard
├─ 监控中 / 已暂停
├─ 当前状态: 检测到 N 人
├─ 打开配置文件
├─ 重新加载配置
├─ 关于
└─ 退出
```

图标状态：

- 绿色：正常监控。
- 黄色：已切换到 VS Code。
- 灰色：暂停。
- 红色：错误。

## 配置

默认配置文件为应用目录下的 `config.json`。首次启动时自动生成。

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

## 错误处理

### 摄像头不可用

- 启动时检测摄像头是否可打开。
- 失败时进入 `ERROR` 状态，托盘图标变红。
- 每 30 秒重试一次。
- 用户可通过托盘菜单重新加载配置或退出。

### 模型加载失败

- 启动时检查模型文件是否存在。
- 模型加载失败时进入 `ERROR` 状态。
- 日志记录模型路径和异常信息。

### VS Code 未找到

- macOS 默认使用 `open -a "Visual Studio Code"`。
- Windows 优先检查正在运行的窗口，再检查常见安装路径。
- 如果自动检测失败，读取 `vscode_path`。
- 如果仍失败，保持当前窗口，不执行切换，并写入日志。

### 原窗口失效

- 切回前检查原窗口是否仍存在。
- 如果原窗口已关闭，清空记录并回到 `MONITORING`。

### 切换抖动

- 检测到 2 个及以上人脸时立即切换。
- 切换到 VS Code 后至少保持 `switch_back_delay` 秒。
- 切回前需要连续 `switch_back_confirm_count` 次检测为 1 人或 0 人。

## 项目结构

```text
touch_fish/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── main_controller.py
│   ├── camera_monitor.py
│   ├── face_detector.py
│   ├── state_manager.py
│   ├── tray_icon.py
│   ├── window_manager/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── macos.py
│   │   └── windows.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       └── logger.py
├── models/
│   └── ultra_light_face_detector.onnx
├── resources/
│   ├── icon_green.png
│   ├── icon_yellow.png
│   ├── icon_gray.png
│   └── icon_red.png
├── config.json
├── requirements.txt
├── build.py
└── README.md
```

## 依赖

核心依赖：

```text
opencv-python
onnxruntime
numpy
pystray
Pillow
```

macOS 依赖：

```text
pyobjc-framework-Cocoa
pyobjc-framework-Quartz
```

Windows 依赖：

```text
pywin32
pygetwindow
```

打包依赖：

```text
pyinstaller
```

## 测试策略

### 单元测试

- `ConfigManager`：默认配置生成、配置覆盖、非法配置处理。
- `StateManager`：状态转换、切回条件、防抖逻辑。
- `FaceDetector`：使用固定测试图片验证人脸计数。
- `WindowManager`：对平台无关接口做 mock 测试。

### 集成测试

- 摄像头可打开并稳定采集帧。
- 模型可加载并完成一次推理。
- 托盘菜单可启动、暂停、恢复、退出监控。
- VS Code 已运行时可以被激活。
- VS Code 未运行时可以被启动。

### 手动验证

- 单人画面不切换。
- 两人画面立即切换到 VS Code。
- 两人离开后切回原窗口。
- 摄像头权限未授予时进入错误状态。
- VS Code 不存在时不破坏当前窗口状态。

## 打包

使用 PyInstaller 打包。

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

## 已确认的产品决策

- 使用本地轻量级人脸检测，不使用云服务。
- 使用系统托盘作为唯一主要界面。
- 检测到 2 个及以上人脸时立即切换。
- 自动切回之前窗口。
- 默认静默运行，不弹系统通知。
- VS Code 行为为智能处理：已运行则激活，未运行则启动。
- 人脸检测默认使用 Ultra-Light-Fast-Generic-Face-Detector，而不是 Haar Cascade。
