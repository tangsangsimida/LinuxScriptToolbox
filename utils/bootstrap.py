"""Project virtual environment bootstrap helpers.

项目虚拟环境引导辅助模块。负责检测、创建虚拟环境并自动切换到虚拟环境中的 Python 解释器。
"""

import os
import subprocess
import sys
from pathlib import Path


def ensure_venv(project_dir: Path) -> None:
    """Run the current script under the project's virtual environment.

    在项目的虚拟环境下运行当前脚本。如果当前已处于虚拟环境中则直接返回，
    否则查找已有的 .venv 并通过 os.execvp 切换到虚拟环境 Python；
    若 .venv 不存在则先创建虚拟环境并安装依赖。

    Args:
        project_dir: The root directory of the project. / 项目的根目录路径。

    Raises:
        SystemExit: If creating the venv or installing dependencies fails. /
            如果创建虚拟环境或安装依赖失败，则抛出 SystemExit。
    """
    # Already inside a virtualenv, nothing to do / 已经在虚拟环境中，无需操作
    if sys.prefix != sys.base_prefix:
        return

    venv_dir = project_dir / ".venv"
    venv_python = venv_dir / "bin" / "python"
    if venv_python.exists():
        # Replace current process with venv Python interpreter / 用虚拟环境 Python 解释器替换当前进程
        os.execvp(str(venv_python), [str(venv_python)] + sys.argv)

    # Venv does not exist yet, set it up first / 虚拟环境尚不存在，先进行设置
    _setup_venv(project_dir, venv_dir, project_dir / "requirements.txt")


def _setup_venv(project_dir: Path, venv_dir: Path, requirements: Path) -> None:
    """Create .venv, install dependencies, and re-exec under venv Python.

    创建 .venv 虚拟环境、安装 requirements.txt 中的依赖，
    然后通过 os.execvp 重新以虚拟环境中的 Python 解释器执行当前脚本。

    Args:
        project_dir: The root directory of the project. / 项目的根目录路径。
        venv_dir: The path to the virtualenv directory. / 虚拟环境目录的路径。
        requirements: The path to the requirements.txt file. / requirements.txt 文件的路径。

    Raises:
        SystemExit: If creating the venv or installing dependencies fails. /
            如果创建虚拟环境或安装依赖失败，则抛出 SystemExit。
    """
    print("Creating virtual environment...")
    # Use stdlib venv module to create the virtual environment / 使用标准库 venv 模块创建虚拟环境
    if subprocess.run([sys.executable, "-m", "venv", str(venv_dir)]).returncode != 0:
        print("Error: Failed to create virtual environment.")
        raise SystemExit(1)

    venv_pip = venv_dir / "bin" / "pip"
    if requirements.exists():
        print("Installing dependencies...")
        # Install project dependencies from requirements.txt / 从 requirements.txt 安装项目依赖
        if subprocess.run([str(venv_pip), "install", "-r", str(requirements)]).returncode != 0:
            print("Error: Failed to install dependencies.")
            raise SystemExit(1)

    venv_python = venv_dir / "bin" / "python"
    # Re-execute the current script using the new venv Python / 使用新虚拟环境的 Python 重新执行当前脚本
    os.execvp(str(venv_python), [str(venv_python)] + sys.argv)
