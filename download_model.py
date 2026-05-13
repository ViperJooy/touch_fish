#!/usr/bin/env python3
"""下载 ONNX 人脸检测模型"""
import os
import sys
import urllib.request


def download_model():
    """下载 Ultra Light Face Detector 模型"""
    print("=" * 50)
    print("下载 ONNX 人脸检测模型")
    print("=" * 50)

    # 模型 URL
    model_url = "https://github.com/Linzaer/Ultra-Light-Fast-Generic-Face-Detector-1MB/raw/master/models/onnx/version-RFB-320.onnx"
    model_path = "models/ultra_light_face_detector.onnx"

    # 检查模型是否已存在
    if os.path.exists(model_path):
        print(f"\n✓ 模型文件已存在: {model_path}")
        file_size = os.path.getsize(model_path) / 1024 / 1024
        print(f"  文件大小: {file_size:.2f} MB")

        response = input("\n是否重新下载？(y/N): ")
        if response.lower() != 'y':
            print("跳过下载")
            return True

    # 确保目录存在
    os.makedirs("models", exist_ok=True)

    # 下载模型
    print(f"\n正在下载模型...")
    print(f"URL: {model_url}")
    print(f"保存到: {model_path}")

    try:
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100)
            downloaded_mb = downloaded / 1024 / 1024
            total_mb = total_size / 1024 / 1024
            print(f"\r下载进度: {percent:.1f}% ({downloaded_mb:.2f}/{total_mb:.2f} MB)", end='')

        urllib.request.urlretrieve(model_url, model_path, show_progress)
        print("\n\n✓ 模型下载成功！")

        # 验证文件
        file_size = os.path.getsize(model_path) / 1024 / 1024
        print(f"  文件大小: {file_size:.2f} MB")

        if file_size < 0.5:
            print("\n✗ 警告: 文件大小异常，可能下载不完整")
            return False

        return True

    except Exception as e:
        print(f"\n\n✗ 下载失败: {e}")
        print("\n备选方案:")
        print("1. 手动下载模型:")
        print(f"   {model_url}")
        print(f"2. 保存到: {model_path}")
        return False


if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
