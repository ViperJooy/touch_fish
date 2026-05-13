"""打包脚本"""
import os
import sys
import platform
import subprocess


def get_platform_separator():
    """获取平台相关的路径分隔符

    Returns:
        PyInstaller --add-data 使用的分隔符
    """
    return ";" if platform.system() == "Windows" else ":"


def build():
    """构建应用"""
    print("=" * 50)
    print("Touch Fish Guard 打包脚本")
    print("=" * 50)

    # 检查必要文件
    print("\n1. 检查必要文件...")
    required_files = [
        "src/main.py",
        "config.json",
        "requirements.txt"
    ]

    for file in required_files:
        if not os.path.exists(file):
            print(f"✗ 缺少必要文件: {file}")
            return False
        print(f"✓ {file}")

    # 检查资源目录
    print("\n2. 检查资源目录...")
    required_dirs = ["resources", "models"]
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"  创建目录: {dir_name}")
            os.makedirs(dir_name, exist_ok=True)
        print(f"✓ {dir_name}")

    # 构建 PyInstaller 命令
    print("\n3. 构建打包命令...")
    separator = get_platform_separator()

    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--add-data=resources{separator}resources",
        f"--add-data=models{separator}models",
        f"--add-data=config.json{separator}.",
        "--name=TouchFishGuard",
        "--clean",
        "src/main.py"
    ]

    print(f"命令: {' '.join(cmd)}")

    # 执行打包
    print("\n4. 开始打包...")
    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            print("\n✓ 打包成功！")

            # 显示输出位置
            if platform.system() == "Windows":
                output_path = "dist\\TouchFishGuard.exe"
            else:
                output_path = "dist/TouchFishGuard"

            print(f"\n可执行文件位置: {output_path}")
            return True
        else:
            print("\n✗ 打包失败")
            return False

    except subprocess.CalledProcessError as e:
        print(f"\n✗ 打包失败: {e}")
        return False
    except FileNotFoundError:
        print("\n✗ 未找到 pyinstaller，请先安装: pip install pyinstaller")
        return False


def clean():
    """清理构建文件"""
    print("\n清理构建文件...")

    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["TouchFishGuard.spec"]

    import shutil

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ 删除目录: {dir_name}")

    for file_name in files_to_clean:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"✓ 删除文件: {file_name}")

    print("清理完成")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean()
    else:
        success = build()
        sys.exit(0 if success else 1)
