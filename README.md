# Touch Fish Guard - 摸鱼守护者

一个智能的工作状态守护工具，当检测到有人靠近时自动切换到 VS Code，保护你的摸鱼时光。

## 功能特性

- 🎥 **实时人脸检测** - 使用 ONNX 模型进行高效的人脸检测
- 🔄 **智能窗口切换** - 检测到多人时自动切换到 VS Code
- ⏱️ **防抖动机制** - 切回原窗口需要延迟和连续确认，避免误操作
- 🎛️ **系统托盘控制** - 通过托盘图标方便地暂停/恢复监控
- ⚙️ **灵活配置** - 支持自定义检测阈值、延迟时间等参数
- 🖥️ **跨平台支持** - 支持 macOS 和 Windows

## 项目结构

```
touch_fish/
├── src/
│   ├── main.py                 # 主入口
│   ├── main_controller.py      # 主控制器
│   ├── state_manager.py        # 状态管理器
│   ├── camera_monitor.py       # 摄像头监控
│   ├── face_detector.py        # 人脸检测器
│   ├── fake_face_detector.py   # 假检测器（测试用）
│   ├── tray_icon.py           # 系统托盘
│   ├── utils/
│   │   ├── config.py          # 配置管理
│   │   └── logger.py          # 日志管理
│   └── window_manager/
│       ├── base.py            # 窗口管理基类
│       ├── macos.py           # macOS 实现
│       ├── windows.py         # Windows 实现
│       └── factory.py         # 工厂函数
├── tests/
│   ├── test_stage1.py         # 配置和日志测试
│   ├── test_stage2.py         # 状态机测试
│   └── test_stage3.py         # 摄像头监控测试
├── models/                     # ONNX 模型目录
├── resources/                  # 资源文件目录
├── logs/                       # 日志目录
├── config.json                 # 配置文件
├── requirements.txt            # Python 依赖
├── build.py                    # 打包脚本
└── README.md                   # 本文件
```

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd touch_fish
```

### 2. 创建虚拟环境

```bash
# 使用 uv（推荐）
uv venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 或使用 venv
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
# 使用 uv
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### 4. 准备模型文件

下载 Ultra Light Face Detector ONNX 模型并放置到 `models/` 目录：

```bash
# 下载模型（示例）
wget https://github.com/Linzaer/Ultra-Light-Fast-Generic-Face-Detector-1MB/raw/master/models/onnx/version-RFB-320.onnx -O models/ultra_light_face_detector.onnx
```

## 配置

编辑 `config.json` 文件：

```json
{
  "vscode_path": "auto",              // VS Code 路径，"auto" 为自动检测
  "camera_index": 0,                  // 摄像头索引
  "detection_interval": 0.5,          // 检测间隔（秒）
  "min_faces_to_switch": 2,           // 触发切换的最小人数
  "switch_back_delay": 2.0,           // 切回延迟（秒）
  "switch_back_confirm_count": 3,     // 切回确认次数
  "face_detector": {
    "backend": "ultra_light_onnx",
    "model_path": "models/ultra_light_face_detector.onnx",
    "confidence_threshold": 0.7,      // 置信度阈值
    "nms_threshold": 0.3              // NMS 阈值
  },
  "auto_start": false,                // 是否开机自启
  "log_level": "INFO"                 // 日志级别
}
```

## 使用

### 开发模式运行

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行应用
python3 -m src.main
```

### 运行测试

```bash
# 测试配置和日志模块
python3 tests/test_stage1.py

# 测试状态机
python3 tests/test_stage2.py

# 测试摄像头监控（需要摄像头）
python3 tests/test_stage3.py
```

### 打包为可执行文件

```bash
# 打包
python3 build.py

# 清理构建文件
python3 build.py clean
```

打包后的可执行文件位于 `dist/` 目录。

## 工作原理

### 状态机

应用有四种状态：

1. **MONITORING（监控中）** - 正常监控状态
2. **SWITCHED（已切换）** - 已切换到 VS Code
3. **PAUSED（已暂停）** - 用户暂停监控
4. **ERROR（错误）** - 发生错误

### 切换逻辑

**切换到 VS Code：**
- 检测到人脸数量 >= `min_faces_to_switch`（默认 2 人）
- 立即切换，无需连续确认

**切回原窗口：**
- 检测到人脸数量 <= 1
- 必须满足延迟时间（`switch_back_delay`）
- 必须连续确认指定次数（`switch_back_confirm_count`）

这种设计避免了频繁切换和误操作。

## 系统要求

### macOS
- macOS 13.0 或更高版本
- Python 3.11+
- 摄像头权限
- 辅助功能权限（用于窗口切换）

### Windows
- Windows 10 或更高版本
- Python 3.11+
- 摄像头权限

## 权限设置

### macOS

1. **摄像头权限**：系统偏好设置 → 安全性与隐私 → 摄像头
2. **辅助功能权限**：系统偏好设置 → 安全性与隐私 → 辅助功能

### Windows

1. **摄像头权限**：设置 → 隐私 → 摄像头

## 故障排除

### 摄像头无法打开

- 检查摄像头是否被其他应用占用
- 检查系统权限设置
- 尝试更改 `camera_index` 配置

### 无法切换窗口

- macOS：检查辅助功能权限
- Windows：以管理员身份运行
- 检查 VS Code 是否已安装

### 模型加载失败

- 确认模型文件存在于 `models/` 目录
- 检查模型文件路径配置
- 确认 ONNX Runtime 已正确安装

## 开发

### 添加新的窗口管理器

1. 在 `src/window_manager/` 创建新的平台实现
2. 继承 `BaseWindowManager`
3. 在 `factory.py` 中注册

### 添加新的人脸检测后端

1. 创建新的检测器类
2. 实现 `detect_faces(frame) -> int` 方法
3. 在配置中指定后端

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 免责声明

本工具仅供学习和研究使用，请遵守公司规章制度和职业道德。
