"""
Foxker 命令行入口点
提供 docker 兼容的命令行接口
"""

import sys
import os
import logging
import argparse
from typing import List, Optional

from .proxy import DockerProxy
from .config import Config

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """
    配置日志级别
    
    Args:
        verbose: 是否启用详细输出
        debug: 是否启用调试输出
    """
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def create_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器
    
    Returns:
        参数解析器
    """
    parser = argparse.ArgumentParser(
        prog="docker",
        description="Foxker - Docker 到 WSL Podman 的代理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  docker run -it ubuntu bash
  docker build -t myimage .
  docker ps -a
  docker images

环境变量:
  FOXKER_CONFIG    配置文件路径
  FOXKER_DEBUG     启用调试模式 (true/false)
  FOXKER_DISTRO    WSL 发行版名称
        """
    )
    
    # Foxker 特有参数
    parser.add_argument(
        "--foxker-info",
        action="store_true",
        help="显示 Foxker 代理信息"
    )
    parser.add_argument(
        "--foxker-check",
        action="store_true",
        help="检查 WSL 和 Podman 可用性"
    )
    parser.add_argument(
        "--foxker-config",
        action="store_true",
        help="显示当前配置"
    )
    parser.add_argument(
        "--foxker-verbose", "-V",
        action="store_true",
        help="启用详细输出"
    )
    parser.add_argument(
        "--foxker-debug",
        action="store_true",
        help="启用调试输出"
    )
    parser.add_argument(
        "--foxker-distro",
        type=str,
        help="指定 WSL 发行版名称"
    )
    parser.add_argument(
        "--foxker-gui",
        action="store_true",
        help="启动图形设置界面"
    )
    
    return parser


def print_info(proxy: DockerProxy) -> None:
    """
    打印代理信息
    
    Args:
        proxy: Docker 代理实例
    """
    info = proxy.get_info()
    
    print("=" * 50)
    print("Foxker - Docker to WSL Podman 代理")
    print("=" * 50)
    print(f"版本: {info['version']}")
    print(f"WSL 可用: {'是' if info['wsl_available'] else '否'}")
    print(f"Podman 可用: {'是' if info['podman_available'] else '否'}")
    
    if info['podman_version']:
        print(f"Podman 版本: {info['podman_version']}")
    
    print("\n配置信息:")
    for key, value in info['config'].items():
        print(f"  {key}: {value}")
    
    print("=" * 50)


def print_config(config: Config) -> None:
    """
    打印当前配置
    
    Args:
        config: 配置实例
    """
    print("当前 Foxker 配置:")
    print("-" * 30)
    for key, value in config.__dict__.items():
        if not key.startswith("_"):
            print(f"  {key}: {value}")


def check_environment(proxy: DockerProxy) -> int:
    """
    检查环境可用性
    
    Args:
        proxy: Docker 代理实例
        
    Returns:
        退出码 (0 表示全部正常)
    """
    print("检查 Foxker 环境...")
    print("-" * 30)
    
    # 检查 WSL
    print("1. 检查 WSL...", end=" ")
    if proxy.check_wsl_available():
        print("✓ 可用")
    else:
        print("✗ 不可用")
        print("   请确保已安装 WSL 并配置了指定的发行版")
        return 1
    
    # 检查 Podman
    print("2. 检查 Podman...", end=" ")
    if proxy.check_podman_available():
        print("✓ 可用")
    else:
        print("✗ 不可用")
        print("   请确保在 WSL 中安装了 Podman")
        return 1
    
    print("-" * 30)
    print("所有检查通过！Foxker 已准备就绪。")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """
    主入口函数
    
    Args:
        argv: 命令行参数，如果为 None 则使用 sys.argv
        
    Returns:
        退出码
    """
    if argv is None:
        argv = sys.argv[1:]
    
    # 解析 Foxker 特有参数
    parser = create_parser()
    
    # 使用 parse_known_args 来保留 Docker 参数
    known_args, docker_args = parser.parse_known_args(argv)
    
    # 配置日志
    setup_logging(
        verbose=known_args.foxker_verbose,
        debug=known_args.foxker_debug or os.environ.get("FOXKER_DEBUG", "").lower() == "true"
    )
    
    # 创建配置
    config = Config()
    
    # 应用命令行配置覆盖
    if known_args.foxker_distro:
        config.wsl_distro = known_args.foxker_distro
    
    # 创建代理
    proxy = DockerProxy(config)
    
    # 处理 Foxker 特有命令
    if known_args.foxker_info:
        print_info(proxy)
        return 0
    
    if known_args.foxker_check:
        return check_environment(proxy)
    
    if known_args.foxker_config:
        print_config(config)
        return 0
    
    # 启动 GUI 设置界面
    if known_args.foxker_gui:
        try:
            from .gui import launch_gui
            launch_gui()
            return 0
        except ImportError as e:
            print(f"错误: 无法启动图形界面 - {e}", file=sys.stderr)
            print("请确保已安装 tkinter", file=sys.stderr)
            return 1
    
    # 如果没有 Docker 参数，显示帮助
    if not docker_args:
        # 执行 podman help
        return proxy.execute(["--help"])
    
    # 执行 Docker 命令
    return proxy.execute(docker_args)


def docker_main() -> int:
    """
    Docker 命令入口点（用于 setuptools 入口）
    
    Returns:
        退出码
    """
    return main()


if __name__ == "__main__":
    sys.exit(main())
