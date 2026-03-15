"""
Docker 命令代理模块
将 Docker 命令转换为 Podman 命令并在 WSL 中执行
"""

import os
import sys
import subprocess
import logging
import shlex
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

from .config import Config
from .path_converter import PathConverter

logger = logging.getLogger(__name__)


class CommandTransformer:
    """Docker 命令转换器，将 Docker 命令转换为 Podman 命令"""
    
    # Docker 到 Podman 的命令映射（大部分命令是相同的）
    COMMAND_ALIASES: Dict[str, str] = {
        # 这些命令在 Podman 中名称相同，无需转换
    }
    
    # 需要路径转换的参数
    PATH_ARGS: set = {
        "-v", "--volume",
        "--mount",
        "--env-file",
        "-w", "--workdir",
        "--cpuset-cpus",  # 某些情况下可能需要路径
    }
    
    # 需要路径转换但参数值在下一个位置
    PATH_VALUE_ARGS: set = {
        "-v", "--volume",
        "--env-file",
        "-w", "--workdir",
    }
    
    # --mount 参数需要特殊处理
    MOUNT_ARGS: set = {"--mount"}
    
    # 构建相关参数
    BUILD_PATH_ARGS: set = {
        "-f", "--file",
        "--build-context",
        "--cache-from",
        "--output",
        "--progress",
        "--secret",
        "--ssh",
        "--context",
    }
    
    # 需要忽略的 Docker 特有参数
    IGNORED_ARGS: set = {
        # Docker Desktop 特有参数，Podman 不支持
    }
    
    # Docker 到 Podman 的参数转换
    ARG_TRANSFORMS: Dict[str, str] = {
        # 大部分参数名称相同
    }
    
    def __init__(self, path_converter: PathConverter):
        """
        初始化命令转换器
        
        Args:
            path_converter: 路径转换器实例
        """
        self.path_converter = path_converter
    
    def transform_command(self, docker_args: List[str], command: str) -> List[str]:
        """
        转换 Docker 命令参数为 Podman 命令参数
        
        Args:
            docker_args: Docker 命令参数列表
            command: Docker 子命令 (如 run, build, ps 等)
            
        Returns:
            转换后的 Podman 命令参数列表
        """
        podman_args = []
        i = 0
        
        while i < len(docker_args):
            arg = docker_args[i]
            
            # 处理 --mount 参数
            if arg in self.MOUNT_ARGS:
                if i + 1 < len(docker_args):
                    mount_value = docker_args[i + 1]
                    converted_mount = self.path_converter.convert_bind_mount(mount_value)
                    podman_args.append(arg)
                    podman_args.append(converted_mount)
                    i += 2
                    continue
            
            # 处理需要路径转换的参数
            if arg in self.PATH_VALUE_ARGS:
                podman_args.append(arg)
                if i + 1 < len(docker_args):
                    path_value = docker_args[i + 1]
                    
                    # -v 参数需要特殊处理（卷挂载）
                    if arg in ("-v", "--volume"):
                        converted = self.path_converter.convert_volume_spec(path_value)
                    else:
                        converted = self.path_converter.windows_to_wsl(path_value)
                    
                    podman_args.append(converted)
                    i += 2
                    continue
            
            # 处理 --mount=xxx 格式（等号形式）
            if arg.startswith("--mount="):
                mount_value = arg[8:]  # 去掉 "--mount="
                converted_mount = self.path_converter.convert_bind_mount(mount_value)
                podman_args.append(f"--mount={converted_mount}")
                i += 1
                continue
            
            # 处理 -v=xxx 格式
            if arg.startswith("-v="):
                volume_value = arg[3:]
                converted_volume = self.path_converter.convert_volume_spec(volume_value)
                podman_args.append(f"-v={converted_volume}")
                i += 1
                continue
            
            # 处理 --volume=xxx 格式
            if arg.startswith("--volume="):
                volume_value = arg[9:]
                converted_volume = self.path_converter.convert_volume_spec(volume_value)
                podman_args.append(f"--volume={converted_volume}")
                i += 1
                continue
            
            # 处理 --env-file=xxx 格式
            if arg.startswith("--env-file="):
                path_value = arg[11:]
                converted = self.path_converter.windows_to_wsl(path_value)
                podman_args.append(f"--env-file={converted}")
                i += 1
                continue
            
            # 处理构建相关参数
            if arg in self.BUILD_PATH_ARGS:
                podman_args.append(arg)
                if i + 1 < len(docker_args):
                    path_value = docker_args[i + 1]
                    converted = self.path_converter.windows_to_wsl(path_value)
                    podman_args.append(converted)
                    i += 2
                    continue
            
            # 处理 -f=xxx 格式
            if arg.startswith("-f="):
                path_value = arg[3:]
                converted = self.path_converter.windows_to_wsl(path_value)
                podman_args.append(f"-f={converted}")
                i += 1
                continue
            
            # 处理 --file=xxx 格式
            if arg.startswith("--file="):
                path_value = arg[7:]
                converted = self.path_converter.windows_to_wsl(path_value)
                podman_args.append(f"--file={converted}")
                i += 1
                continue
            
            # 其他参数直接传递
            podman_args.append(arg)
            i += 1
        
        # 对于 build 命令，转换最后的构建上下文路径
        if command == "build" and podman_args:
            last_arg = podman_args[-1]
            # 检查最后一个参数是否是路径（不是选项）
            if not last_arg.startswith("-"):
                converted_context = self.path_converter.convert_build_context(last_arg)
                podman_args[-1] = converted_context
        
        return podman_args


class DockerProxy:
    """
    Docker 命令代理类
    拦截 Docker 命令，转换为 Podman 命令并在 WSL 中执行
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化代理
        
        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        self.config = config or Config()
        self.path_converter = PathConverter(self.config)
        self.command_transformer = CommandTransformer(self.path_converter)
        
        # 设置日志
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """配置日志系统"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # 配置根日志记录器
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            filename=self.config.log_file
        )
        
        logger.info("Foxker Docker 代理已初始化")
        logger.debug(f"WSL 发行版: {self.config.wsl_distro}")
        logger.debug(f"Podman 路径: {self.config.podman_path}")
    
    def build_wsl_command(self, docker_args: List[str]) -> List[str]:
        """
        构建 WSL 命令
        
        Args:
            docker_args: Docker 命令参数列表
            
        Returns:
            完整的 WSL 命令列表
        """
        # 提取 Docker 子命令
        command = docker_args[0] if docker_args else ""
        
        # 转换参数
        transformed_args = self.command_transformer.transform_command(
            docker_args[1:], command
        ) if len(docker_args) > 1 else []
        
        # 构建 Podman 命令
        podman_cmd = [self.config.podman_path, command] + transformed_args
        
        # 构建 WSL 命令
        wsl_cmd = [
            "wsl",
            "-d", self.config.wsl_distro,
            "--"
        ] + podman_cmd
        
        return wsl_cmd
    
    def execute(self, docker_args: List[str]) -> int:
        """
        执行代理命令
        
        Args:
            docker_args: Docker 命令参数列表
            
        Returns:
            命令退出码
        """
        if not docker_args:
            # 无参数时显示帮助
            docker_args = ["--help"]
        
        # 构建命令
        wsl_cmd = self.build_wsl_command(docker_args)
        
        logger.info(f"执行命令: {' '.join(wsl_cmd)}")
        
        try:
            # 直接执行，继承标准输入输出
            result = subprocess.run(
                wsl_cmd,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
                timeout=self.config.command_timeout
            )
            
            logger.debug(f"命令退出码: {result.returncode}")
            return result.returncode
            
        except subprocess.TimeoutExpired:
            logger.error(f"命令执行超时 ({self.config.command_timeout}秒)")
            print(f"错误: 命令执行超时", file=sys.stderr)
            return 124  # timeout 命令的标准退出码
        
        except FileNotFoundError:
            logger.error("WSL 命令未找到，请确保已安装 WSL")
            print("错误: WSL 命令未找到，请确保已安装 WSL", file=sys.stderr)
            return 127
        
        except KeyboardInterrupt:
            logger.info("用户中断执行")
            return 130  # SIGINT 的标准退出码
        
        except Exception as e:
            logger.exception(f"命令执行失败: {e}")
            print(f"错误: {e}", file=sys.stderr)
            return 1
    
    def execute_with_output(self, docker_args: List[str]) -> Tuple[int, str, str]:
        """
        执行命令并捕获输出
        
        Args:
            docker_args: Docker 命令参数列表
            
        Returns:
            (退出码, 标准输出, 标准错误) 元组
        """
        if not docker_args:
            docker_args = ["--help"]
        
        wsl_cmd = self.build_wsl_command(docker_args)
        
        logger.debug(f"执行命令（捕获输出）: {' '.join(wsl_cmd)}")
        
        try:
            result = subprocess.run(
                wsl_cmd,
                capture_output=True,
                text=True,
                timeout=self.config.command_timeout
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"命令执行超时 ({self.config.command_timeout}秒)")
            return 124, "", "命令执行超时"
        
        except FileNotFoundError:
            logger.error("WSL 命令未找到")
            return 127, "", "WSL 命令未找到"
        
        except Exception as e:
            logger.exception(f"命令执行失败: {e}")
            return 1, "", str(e)
    
    def check_wsl_available(self) -> bool:
        """
        检查 WSL 是否可用
        
        Returns:
            WSL 是否可用
        """
        try:
            result = subprocess.run(
                ["wsl", "-l", "-v"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # 检查指定的发行版是否存在
                return self.config.wsl_distro.lower() in result.stdout.lower()
            
            return False
            
        except Exception as e:
            logger.error(f"检查 WSL 可用性失败: {e}")
            return False
    
    def check_podman_available(self) -> bool:
        """
        检查 Podman 是否在 WSL 中可用
        
        Returns:
            Podman 是否可用
        """
        try:
            result = subprocess.run(
                ["wsl", "-d", self.config.wsl_distro, "--", 
                 self.config.podman_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"Podman 版本: {result.stdout.strip()}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查 Podman 可用性失败: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取代理信息
        
        Returns:
            包含代理信息的字典
        """
        info = {
            "version": "1.0.0",
            "wsl_available": self.check_wsl_available(),
            "podman_available": False,
            "podman_version": None,
            "config": {
                "wsl_distro": self.config.wsl_distro,
                "podman_path": self.config.podman_path,
                "windows_drives_prefix": self.config.windows_drives_prefix,
            }
        }
        
        if info["wsl_available"]:
            exit_code, stdout, _ = self.execute_with_output(["--version"])
            if exit_code == 0:
                info["podman_available"] = True
                info["podman_version"] = stdout.strip()
        
        return info
