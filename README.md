# Foxker

一个适用于 Windows 的 Docker 便携指令客户端，将 Docker 命令代理到 WSL Podman。

## 简介

Foxker 是一个轻量级的 Docker 命令代理工具，它将 Windows 上的 `docker` 命令透明地代理到 WSL (Windows Subsystem for Linux) 中的 Podman。无需安装庞大的 Docker Desktop，即可在 Windows 上使用熟悉的 Docker 命令。

**核心理念：** 拒绝使用官方庞大的 Docker Desktop，用 Python 实现一个简洁、便携的替代方案。

## 功能特性

- **透明代理** - Docker 命令无缝转换为 Podman 命令
- **路径自动转换** - Windows 路径自动转换为 WSL 路径
- **卷挂载支持** - 正确处理 `-v` 和 `--mount` 参数
- **便携式设计** - 无需安装，可直接运行
- **GUI 设置界面** - 简易的图形化配置管理
- **sudo 模式** - 解决 WSL Podman 的 systemd 问题

## 系统要求

- Windows 10/11
- WSL 2 (已安装 Debian 或其他 Linux 发行版)
- Python 3.8+
- Podman (在 WSL 中安装)

## 安装

### 方式 1: 使用安装脚本

```powershell
# PowerShell
.\install.ps1

# 或添加到 PATH
.\install.ps1 -AddToPath

# 批处理
.\install.bat
```

### 方式 2: pip 安装

```powershell
pip install -e .
```

### 方式 3: 便携式使用

```powershell
# 直接运行
python -m foxker [docker命令]

# 或使用生成的脚本
.\docker.bat [docker命令]
```

## 使用方法

### 基本 Docker 命令

```powershell
# 查看版本
docker -v

# 列出容器
docker ps -a

# 列出镜像
docker images

# 运行容器
docker run -it ubuntu bash

# 构建镜像
docker build -t myimage .

# 卷挂载 (Windows 路径自动转换)
docker run -v C:\data:/app myimage

# 使用 --mount 参数
docker run --mount type=bind,source=C:\data,target=/app myimage
```

### Foxker 特有命令

```powershell
# 显示代理信息
docker --foxker-info

# 检查环境可用性
docker --foxker-check

# 显示当前配置
docker --foxker-config

# 启动 GUI 设置界面
docker --foxker-gui

# 启用详细输出
docker --foxker-verbose ps

# 启用调试输出
docker --foxker-debug ps

# 指定 WSL 发行版
docker --foxker-distro ubuntu ps
```

### GUI 设置界面

```powershell
# 启动 GUI
foxker-gui

# 或
docker --foxker-gui
```

GUI 界面功能：
- WSL 发行版选择
- Podman 路径配置
- sudo 模式开关
- 命令超时设置
- 路径映射配置
- 环境状态检查

## 配置

配置文件位于 `~/.foxker/config.json`

### 配置选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `wsl_distro` | string | `debian` | WSL 发行版名称 |
| `podman_path` | string | `podman` | Podman 命令路径 |
| `use_sudo` | bool | `false` | 是否使用 sudo 运行 Podman |
| `windows_drives_prefix` | string | `/mnt` | Windows 驱动器挂载前缀 |
| `mount_point` | string | `/tmp/foxker-mounts` | 临时挂载点 |
| `command_timeout` | int | `300` | 命令超时时间（秒） |
| `stream_buffer_size` | int | `8192` | 流缓冲区大小 |
| `log_level` | string | `INFO` | 日志级别 |
| `log_file` | string | `null` | 日志文件路径 |

### 环境变量

| 变量 | 说明 |
|------|------|
| `FOXKER_CONFIG` | 配置文件路径 |
| `FOXKER_DEBUG` | 启用调试模式 (true/false) |
| `FOXKER_DISTRO` | WSL 发行版名称 |

## 路径转换

Foxker 自动将 Windows 路径转换为 WSL 路径：

| Windows 路径 | WSL 路径 |
|--------------|----------|
| `C:\Users\test` | `/mnt/c/Users/test` |
| `D:\Projects\app` | `/mnt/d/Projects/app` |
| `C:/data/file.txt` | `/mnt/c/data/file.txt` |

### 卷挂载转换

```powershell
# Windows 命令
docker run -v C:\data:/app myimage

# 转换后
wsl -d debian -- podman run -v /mnt/c/data:/app myimage
```

## 常见问题

### 1. systemd 相关错误

如果遇到 `Failed to start the systemd user session` 错误：

**解决方案 A: 启用 sudo 模式**

在 GUI 中勾选 "使用 sudo 运行 Podman"，或编辑配置文件：
```json
{
    "use_sudo": true
}
```

**解决方案 B: 在 WSL 中启用 linger**

```bash
# 在 WSL 中执行
sudo loginctl enable-linger $USER

# 然后在 Windows 中重启 WSL
wsl --shutdown
```

### 2. WSL 配置警告

如果看到 `wsl2.systemd: 键"2"未知` 警告：

确保 `.wslconfig` 文件格式正确：
```ini
[wsl2]
systemd=true
```

### 3. 权限问题

如果遇到权限问题，可以：
1. 启用 `use_sudo` 配置
2. 或将用户添加到 WSL 的 podman 组

## 项目结构

```
foxker/
├── foxker/
│   ├── __init__.py          # 包入口
│   ├── __main__.py          # python -m foxker 支持
│   ├── cli.py               # 命令行接口
│   ├── config.py            # 配置管理
│   ├── path_converter.py    # 路径转换
│   ├── proxy.py             # Docker 命令代理
│   ├── gui.py               # GUI 设置界面
│   ├── default_config.json  # 默认配置
│   └── foxker.ico           # 图标
├── install.ps1              # PowerShell 安装脚本
├── install.bat              # 批处理安装脚本
├── pyproject.toml           # 项目配置
└── README.md                # 说明文档
```

## 开发

### 安装开发依赖

```powershell
pip install -e ".[dev]"
```

### 运行测试

```powershell
python -m pytest tests/ -v
```

### 代码格式化

```powershell
black foxker/
isort foxker/
```

### 类型检查

```powershell
mypy foxker/
```

## 许可证

MIT License

## 致谢

- [Podman](https://podman.io/) - 无守护进程的容器引擎
- [WSL](https://learn.microsoft.com/en-us/windows/wsl/) - Windows Subsystem for Linux
