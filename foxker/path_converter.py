"""
路径转换模块
将 Windows 路径转换为 WSL 路径，处理挂载卷映射
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from urllib.parse import unquote

from .config import Config

logger = logging.getLogger(__name__)


class PathConverter:
    """Windows 路径到 WSL 路径转换器"""
    
    # Windows 路径正则表达式
    WINDOWS_PATH_PATTERN = re.compile(
        r'^([a-zA-Z]):([\\\/].*)$'  # 匹配 C:\path 或 C:/path
    )
    
    # UNC 路径正则表达式 (网络路径)
    UNC_PATH_PATTERN = re.compile(
        r'^\\\\([^\\]+)\\(.+)$'  # 匹配 \\server\share\path
    )
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化路径转换器
        
        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        self.config = config or Config()
        self._mount_cache: dict = {}  # 挂载点缓存
    
    def windows_to_wsl(self, windows_path: str) -> str:
        """
        将 Windows 路径转换为 WSL 路径
        
        Args:
            windows_path: Windows 路径 (如 C:\\Users\\test 或 C:/Users/test)
            
        Returns:
            WSL 路径 (如 /mnt/c/Users/test)
            
        Raises:
            ValueError: 如果路径格式无效
        """
        if not windows_path:
            return windows_path
        
        # 处理 URL 编码的路径
        windows_path = unquote(windows_path)
        
        # 如果已经是 WSL/Unix 路径（以 / 开头），直接返回
        if windows_path.startswith("/"):
            logger.debug(f"路径已是 WSL 格式: {windows_path}")
            return windows_path
        
        # 检查是否为 UNC 路径 (\\server\share)
        if windows_path.startswith("\\\\"):
            unc_match = self.UNC_PATH_PATTERN.match(windows_path)
            if unc_match:
                server, share_path = unc_match.groups()
                wsl_path = f"//{server}/{share_path.replace('\\', '/')}"
                logger.debug(f"UNC 路径转换: {windows_path} -> {wsl_path}")
                return wsl_path
        
        # 检查是否为标准 Windows 路径 (C:\ 或 C:/)
        # 使用原始路径进行匹配，不预先转换分隔符
        win_match = self.WINDOWS_PATH_PATTERN.match(windows_path)
        if win_match:
            drive_letter, path = win_match.groups()
            # 将路径中的反斜杠转换为正斜杠
            path = path.replace("\\", "/")
            drive_lower = drive_letter.lower()
            wsl_path = f"{self.config.windows_drives_prefix}/{drive_lower}{path}"
            logger.debug(f"Windows 路径转换: {windows_path} -> {wsl_path}")
            return wsl_path
        
        # 如果是相对路径或其他格式，直接返回
        logger.debug(f"路径无需转换: {windows_path}")
        return windows_path
    
    def convert_volume_spec(self, volume_spec: str) -> str:
        """
        转换 Docker 卷挂载规格
        
        支持格式:
        - host_path:container_path
        - host_path:container_path:ro
        - host_path:container_path:rw,Z
        
        Args:
            volume_spec: Docker 卷挂载规格
            
        Returns:
            转换后的 Podman 卷挂载规格
        """
        # 查找容器路径的起始位置（以 / 开头）
        # 容器路径总是以 / 开头，所以找到 ":/" 序列
        container_start = volume_spec.find(":/")
        
        if container_start == -1:
            # 没有找到容器路径，可能是命名卷，直接返回
            return volume_spec
        
        # 主机路径是容器路径之前的部分（不包括冒号）
        host_path = volume_spec[:container_start]
        
        # 剩余部分（包括容器路径）
        remaining = volume_spec[container_start + 1:]  # 跳过冒号
        
        # 查找选项部分（容器路径后面的冒号）
        # 容器路径中可能包含多个路径段，但不会有额外的冒号
        option_colon = remaining.find(":")
        if option_colon != -1:
            container_path = remaining[:option_colon]
            options = remaining[option_colon + 1:]
        else:
            container_path = remaining
            options = ""
        
        # 转换主机路径
        converted_host_path = self.windows_to_wsl(host_path)
        
        # 重建卷规格
        result = f"{converted_host_path}:{container_path}"
        if options:
            result += ":" + options
        
        logger.debug(f"卷规格转换: {volume_spec} -> {result}")
        return result
    
    def convert_bind_mount(self, mount_arg: str) -> str:
        """
        转换 --mount 参数中的绑定挂载
        
        格式: type=bind,source=<host_path>,target=<container_path>[,options...]
        
        Args:
            mount_arg: --mount 参数值
            
        Returns:
            转换后的 --mount 参数值
        """
        if not mount_arg.startswith("type=bind"):
            # 非绑定挂载，直接返回
            return mount_arg
        
        # 解析参数
        params = {}
        for part in mount_arg.split(","):
            if "=" in part:
                key, value = part.split("=", 1)
                params[key] = value
        
        # 转换 source 路径
        if "source" in params:
            params["source"] = self.windows_to_wsl(params["source"])
        elif "src" in params:
            params["src"] = self.windows_to_wsl(params["src"])
        
        # 重建参数
        result_parts = [f"{k}={v}" for k, v in params.items()]
        result = ",".join(result_parts)
        
        logger.debug(f"挂载参数转换: {mount_arg} -> {result}")
        return result
    
    def convert_env_file(self, env_file_path: str) -> str:
        """
        转换 --env-file 参数中的路径
        
        Args:
            env_file_path: 环境变量文件路径
            
        Returns:
            转换后的路径
        """
        return self.windows_to_wsl(env_file_path)
    
    def convert_build_context(self, context_path: str) -> str:
        """
        转换构建上下文路径
        
        Args:
            context_path: 构建上下文路径
            
        Returns:
            转换后的路径
        """
        return self.windows_to_wsl(context_path)
    
    def convert_file_path(self, file_path: str) -> str:
        """
        转换通用文件路径
        
        Args:
            file_path: 文件路径
            
        Returns:
            转换后的路径
        """
        return self.windows_to_wsl(file_path)
    
    def is_windows_path(self, path: str) -> bool:
        """
        检查是否为 Windows 路径
        
        Args:
            path: 待检查的路径
            
        Returns:
            是否为 Windows 路径
        """
        return bool(
            self.WINDOWS_PATH_PATTERN.match(path) or
            self.UNC_PATH_PATTERN.match(path)
        )
    
    def get_current_wsl_path(self) -> str:
        """
        获取当前工作目录的 WSL 路径
        
        Returns:
            当前目录的 WSL 路径
        """
        cwd = os.getcwd()
        return self.windows_to_wsl(cwd)
