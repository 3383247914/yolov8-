import os
import sys
import subprocess
import platform
import shutil


def fix_qt_environment():
    """修复PySide6/Qt环境问题"""
    print("=" * 50)
    print("开始修复Qt环境问题")
    print("=" * 50)

    # 1. 确保安装了PySide6
    try:
        import PySide6
        print(f"PySide6已安装: {PySide6.__version__}")
    except ImportError:
        print("PySide6未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PySide6"])
        import PySide6
        print(f"PySide6安装完成: {PySide6.__version__}")

    # 2. 设置环境变量
    pyside6_dir = os.path.dirname(PySide6.__file__)
    plugins_path = os.path.join(pyside6_dir, "plugins")
    bin_path = os.path.join(pyside6_dir, "bin")

    print(f"PySide6目录: {pyside6_dir}")
    print(f"插件路径: {plugins_path}")

    # 设置环境变量
    os.environ["QT_PLUGIN_PATH"] = plugins_path
    if platform.system() == "Windows":
        os.environ["PATH"] = bin_path + os.pathsep + os.environ["PATH"]

    print("环境变量设置完成")

    # 3. 检查关键文件是否存在
    required_files = [
        os.path.join(plugins_path, "platforms", "qwindows.dll"),
        os.path.join(bin_path, "Qt6Core.dll")
    ]

    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"找到: {file_path}")
        else:
            print(f"警告: 未找到 {file_path}")
            all_files_exist = False

    if not all_files_exist:
        print("\n关键文件缺失，尝试重新安装PySide6...")
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "PySide6"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PySide6"])
        print("PySide6重新安装完成")

    print("=" * 50)
    print("修复完成! 请重新运行应用程序")
    print("=" * 50)


if __name__ == "__main__":
    fix_qt_environment()