"""
Foxker - Docker 到 WSL Podman 代理工具
将 Windows 上的 docker 命令代理到 WSL Debian 的 podman
"""

__version__ = "1.0.0"
__author__ = "Foxker Team"

from .proxy import DockerProxy
from .path_converter import PathConverter
from .config import Config

__all__ = ["DockerProxy", "PathConverter", "Config", "launch_gui"]


def launch_gui():
    """启动图形设置界面"""
    from .gui import launch_gui as _launch
    _launch()
