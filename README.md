# Touch Fish Guard - 摸鱼守护者

一个智能的工作状态守护工具，检测到无人或有人靠近时自动切换到 VS Code，保护你的摸鱼时光。

## 功能特性

- 🎥 **实时人脸检测** - 使用 ONNX 模型进行高效的人脸检测
- 🔄 **即时窗口切换** - 人脸数变化时立即切换，无延迟
- 🎛️ **系统托盘控制** - 实时显示人脸数，方便暂停/恢复监控
- 🖥️ **跨平台支持** - 支持 macOS

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
├── tests/                      # 测试目录
├── models/                     # ONNX 模型目录
├── resources/                  # 资源文件目录
├── logs/                       # 日志目录
├── config.json                 # 配置文件
├── pyproject.toml              # Python 项目配置与依赖
├── uv.lock                     # uv 锁定文件
├── build.py                    # 打包脚本
└── README.md                   # 本文件
```

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd touch_fish
```

### 2. 安装依赖并创建虚拟环境

```bash
uv sync
```

### 3. 准备模型文件

```bash
uv run python download_model.py
```

## 配置

编辑 `config.json` 文件：

```json
{
  "target_apps": [
    {"min_faces": 2, "app": "Visual Studio Code"}
  ],
  "camera_index": 0,
  "detection_interval": 0.3,
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

### 配置文件说明

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `target_apps` | `[{"min_faces": 2, "app": "Visual Studio Code"}]` | 目标应用配置 |
| `camera_index` | `0` | 摄像头索引 |
| `detection_interval` | `0.3` | 检测间隔（秒） |
| `face_detector.backend` | `ultra_light_onnx` | 人脸检测后端 |
| `auto_start` | `false` | 是否开机自启 |
| `log_level` | `INFO` | 日志级别 |

### 触发逻辑

| 人脸数 | 行为 |
|--------|------|
| **0 人**（无人看守） | 切换到 VS Code |
| **1 人**（正常使用） | 不操作；如果在 VS Code 上则切回原窗口 |
| **2+ 人**（有人靠近） | 切换到 VS Code |

> 只在人脸数**变化**时触发操作，同一人数不会重复切换。

### 目标应用配置

`target_apps` 支持多个应用条目，通过 `min_faces` 匹配不同人数：

```json
{
  "target_apps": [
    {"min_faces": 0, "app": "Visual Studio Code"},
    {"min_faces": 1, "app": "Google Chrome"},
    {"min_faces": 2, "app": "Visual Studio Code"}
  ]
}
```

每个条目的可选字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `min_faces` | 是 | 触发该应用的最小人脸数 |
| `app` | 是 | 应用名称（用于匹配窗口和启动） |
| `launch_command` | 否 | 自定义启动路径 |

## 使用

### 运行

```bash
uv run python -m src.main
```

### 运行测试

```bash
uv run python tests/test_stage1.py
uv run python tests/test_stage2.py
uv run python tests/test_stage3.py
```

### 打包

```bash
uv sync --extra build
uv run python build.py
```

## 工作原理

### 状态机

应用有三种状态：

1. **MONITORING（监控中）** - 正常监控状态
2. **SWITCHED（已切换）** - 已切换到 VS Code
3. **PAUSED（已暂停）** - 用户暂停监控

### 切换逻辑

系统持续监控摄像头画面，当检测到的人脸数**发生改变**时：

- **0 人或 2+ 人** → 切换到目标应用（如 VS Code）
- **1 人** → 如果当前在 VS Code 上，切回原窗口

每次切换前会记录当前窗口，切回时重新激活它。

### 日志格式

```
🟢 人脸: 1          ← 人脸数变化时
🔄 切换到 VS Code  ────────────────  ← 切换目标应用
↩️ 切回 Ghostty  ────────────────   ← 切回原窗口
```

## 系统要求

### macOS
- macOS 13.0 或更高版本
- Python 3.11+
- 摄像头权限
- 辅助功能权限（用于窗口切换）

## 权限设置

### macOS

1. **摄像头权限**：系统设置 → 隐私与安全性 → 摄像头
2. **辅助功能权限**：系统设置 → 隐私与安全性 → 辅助功能

## 故障排除

### 摄像头无法打开
- 检查摄像头是否被其他应用占用
- 检查系统权限设置
- 尝试更改 `camera_index` 配置

### 无法切换窗口
- macOS：检查辅助功能权限
- 检查目标应用是否已安装

## 许可证

MIT License

## 免责声明

本工具仅供学习和研究使用，请遵守公司规章制度和职业道德。