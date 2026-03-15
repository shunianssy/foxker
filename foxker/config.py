"""
配置管理模块
管理 WSL 发行版、路径映射等配置
"""

import json
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """配置类，管理所有设置"""
    
    # WSL 配置
    wsl_distro: str = "debian"  # WSL 发行版名称
    podman_path: str = "podman"  # podman 命令路径
    
    # 路径映射配置
    windows_drives_prefix: str = "/mnt"  # Windows 驱动器挂载前缀
    mount_point: str = "/tmp/foxker-mounts"  # 临时挂载点
    
    # 性能配置
    command_timeout: int = 300  # 命令超时时间（秒）
    stream_buffer_size: int = 8192  # 流缓冲区大小
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # 配置文件路径
    _config_path: str = field(default="", repr=False)
    
    def __post_init__(self):
        """初始化后处理"""
        self._config_path = self._get_default_config_path()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 优先使用环境变量指定的路径
        if "FOXKER_CONFIG" in os.environ:
            return os.environ["FOXKER_CONFIG"]
        
        # 其次使用用户目录下的配置
        config_dir = Path.home() / ".foxker"
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / "config.json")
    
    def _load_config(self) -> None:
        """从配置文件加载配置"""
        config_path = Path(self._config_path)
        
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                
                # 更新配置
                for key, value in config_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                
                logger.info(f"配置已从 {config_path} 加载")
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}，使用默认配置")
        else:
            logger.info("配置文件不存在，使用默认配置")
            self.save()
    
    def save(self) -> None:
        """保存配置到文件"""
        config_path = Path(self._config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 排除私有属性
        config_data = {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }
        
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到 {config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """从指定文件加载配置"""
        config = cls()
        config._config_path = config_path
        config._load_config()
        return config
    
    def update(self, **kwargs) -> None:
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"配置已更新: {key} = {value}")
