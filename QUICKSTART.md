# Touch Fish Guard - 快速开始指南

## 快速启动（3 步）

### 1. 安装依赖

```bash
# 创建虚拟环境
uv venv
source .venv/bin/activate  # macOS/Linux

# 安装依赖
uv pip install -r requirements.txt
```

### 2. 下载模型

```bash
# 使用下载脚本
python3 download_model.py

# 或手动下载
wget https://github.com/Linzaer/Ultra-Light-Fast-Generic-Face-Detector-1MB/raw/master/models/onnx/version-RFB-320.onnx -O models/ultra_light_face_detector.onnx
```

### 3. 运行应用

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行
python3 -m src.main
```

## 测试

```bash
# 测试配置和日志
python3 tests/test_stage1.py

# 测试状态机
python3 tests/test_stage2.py

# 测试摄像头（需要摄像头硬件）
python3 tests/test_stage3.py
```

## 打包

```bash
# 打包为可执行文件
python3 build.py

# 运行打包后的应用
./dist/TouchFishGuard  # macOS
# 或
dist\TouchFishGuard.exe  # Windows
```

## 配置

编辑 `config.json` 调整参数：

```json
{
  "camera_index": 0,           // 摄像头索引
  "detection_interval": 0.5,   // 检测间隔（秒）
  "min_faces_to_switch": 2,    // 触发切换的人数
  "switch_back_delay": 2.0,    // 切回延迟（秒）
  "switch_back_confirm_count": 3  // 切回确认次数
}
```

## 权限设置

### macOS
1. 系统偏好设置 → 安全性与隐私 → 摄像头 → 允许访问
2. 系统偏好设置 → 安全性与隐私 → 辅助功能 → 允许访问

### Windows
1. 设置 → 隐私 → 摄像头 → 允许访问

## 使用托盘图标

应用启动后会在系统托盘显示图标：

- 🟢 绿色 = 监控中
- 🟡 黄色 = 已切换到 VS Code
- ⚪ 灰色 = 已暂停
- 🔴 红色 = 错误

右键点击托盘图标可以：
- 暂停/恢复监控
- 打开配置文件
- 重新加载配置
- 退出应用

## 故障排除

### 摄像头无法打开
- 检查摄像头是否被其他应用占用
- 检查系统权限设置
- 尝试更改 `camera_index` 为 1 或 2

### 无法切换窗口
- macOS: 检查辅助功能权限
- Windows: 以管理员身份运行

### 模型加载失败
- 确认模型文件存在: `ls -lh models/ultra_light_face_detector.onnx`
- 重新下载模型: `python3 download_model.py`

## 更多信息

详细文档请查看 [README.md](README.md)
