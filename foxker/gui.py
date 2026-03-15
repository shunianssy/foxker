"""
Foxker GUI 设置界面
使用 Tkinter 实现的简易配置管理界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import sys
from typing import Optional, Callable

from .config import Config


class FoxkerGUI:
    """Foxker 设置界面类"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化 GUI
        
        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        self.config = config or Config()
        self.root: Optional[tk.Tk] = None
        self.log_text: Optional[scrolledtext.ScrolledText] = None  # 预先声明
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """设置用户界面"""
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("Foxker 设置")
        self.root.geometry("550x500")
        self.root.resizable(True, True)
        
        # 设置窗口图标
        self._set_icon()
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建笔记本（选项卡容器）
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建各个选项卡
        self._create_general_tab(notebook)
        self._create_paths_tab(notebook)
        self._create_status_tab(notebook)
        
        # 创建底部按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 保存按钮
        save_btn = ttk.Button(
            button_frame, 
            text="保存设置", 
            command=self._save_config,
            width=15
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # 重置按钮
        reset_btn = ttk.Button(
            button_frame, 
            text="重置默认", 
            command=self._reset_config,
            width=15
        )
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # 检查环境按钮
        check_btn = ttk.Button(
            button_frame, 
            text="检查环境", 
            command=self._check_environment,
            width=15
        )
        check_btn.pack(side=tk.LEFT, padx=5)
        
        # 关闭按钮
        close_btn = ttk.Button(
            button_frame, 
            text="关闭", 
            command=self.root.quit,
            width=15
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            main_frame, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=(5, 0))
    
    def _create_general_tab(self, notebook: ttk.Notebook) -> None:
        """创建常规设置选项卡"""
        general_frame = ttk.Frame(notebook, padding="10")
        notebook.add(general_frame, text="常规设置")
        
        # WSL 发行版设置
        wsl_frame = ttk.LabelFrame(general_frame, text="WSL 设置", padding="10")
        wsl_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(wsl_frame, text="WSL 发行版:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.wsl_distro_var = tk.StringVar(value=self.config.wsl_distro)
        self.wsl_distro_combo = ttk.Combobox(
            wsl_frame, 
            textvariable=self.wsl_distro_var,
            width=30
        )
        self.wsl_distro_combo.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        
        # 刷新发行版列表按钮
        refresh_btn = ttk.Button(
            wsl_frame,
            text="刷新",
            command=self._refresh_wsl_distros,
            width=8
        )
        refresh_btn.grid(row=0, column=2, padx=5)
        
        # 初始加载发行版列表
        self._refresh_wsl_distros()
        
        wsl_frame.columnconfigure(1, weight=1)
        
        # Podman 设置
        podman_frame = ttk.LabelFrame(general_frame, text="Podman 设置", padding="10")
        podman_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(podman_frame, text="Podman 路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.podman_path_var = tk.StringVar(value=self.config.podman_path)
        podman_entry = ttk.Entry(podman_frame, textvariable=self.podman_path_var, width=35)
        podman_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        
        podman_frame.columnconfigure(1, weight=1)
        
        # 性能设置
        perf_frame = ttk.LabelFrame(general_frame, text="性能设置", padding="10")
        perf_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(perf_frame, text="命令超时 (秒):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.timeout_var = tk.StringVar(value=str(self.config.command_timeout))
        timeout_spinbox = ttk.Spinbox(
            perf_frame, 
            from_=10, 
            to=3600, 
            textvariable=self.timeout_var,
            width=10
        )
        timeout_spinbox.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(perf_frame, text="缓冲区大小:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.buffer_var = tk.StringVar(value=str(self.config.stream_buffer_size))
        buffer_spinbox = ttk.Spinbox(
            perf_frame, 
            from_=1024, 
            to=65536, 
            increment=1024,
            textvariable=self.buffer_var,
            width=10
        )
        buffer_spinbox.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
    
    def _create_paths_tab(self, notebook: ttk.Notebook) -> None:
        """创建路径设置选项卡"""
        paths_frame = ttk.Frame(notebook, padding="10")
        notebook.add(paths_frame, text="路径设置")
        
        # 路径映射设置
        mapping_frame = ttk.LabelFrame(paths_frame, text="路径映射", padding="10")
        mapping_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mapping_frame, text="Windows 驱动器前缀:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.drives_prefix_var = tk.StringVar(value=self.config.windows_drives_prefix)
        prefix_entry = ttk.Entry(mapping_frame, textvariable=self.drives_prefix_var, width=30)
        prefix_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        
        ttk.Label(mapping_frame, text="示例: /mnt (将 C:\\ 转换为 /mnt/c/)").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=2
        )
        
        mapping_frame.columnconfigure(1, weight=1)
        
        # 挂载点设置
        mount_frame = ttk.LabelFrame(paths_frame, text="临时挂载点", padding="10")
        mount_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mount_frame, text="挂载点路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.mount_point_var = tk.StringVar(value=self.config.mount_point)
        mount_entry = ttk.Entry(mount_frame, textvariable=self.mount_point_var, width=30)
        mount_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        
        mount_frame.columnconfigure(1, weight=1)
        
        # 路径转换测试
        test_frame = ttk.LabelFrame(paths_frame, text="路径转换测试", padding="10")
        test_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(test_frame, text="Windows 路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.test_input_var = tk.StringVar(value="C:\\Users\\test\\project")
        test_input = ttk.Entry(test_frame, textvariable=self.test_input_var, width=40)
        test_input.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        
        test_btn = ttk.Button(test_frame, text="转换", command=self._test_path_conversion)
        test_btn.grid(row=0, column=2, padx=5)
        
        ttk.Label(test_frame, text="WSL 路径:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.test_output_var = tk.StringVar()
        test_output = ttk.Entry(test_frame, textvariable=self.test_output_var, width=40, state="readonly")
        test_output.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        
        test_frame.columnconfigure(1, weight=1)
    
    def _create_status_tab(self, notebook: ttk.Notebook) -> None:
        """创建状态信息选项卡"""
        status_frame = ttk.Frame(notebook, padding="10")
        notebook.add(status_frame, text="状态信息")
        
        # 环境状态
        env_frame = ttk.LabelFrame(status_frame, text="环境状态", padding="10")
        env_frame.pack(fill=tk.X, pady=5)
        
        # WSL 状态
        self.wsl_status_var = tk.StringVar(value="检查中...")
        ttk.Label(env_frame, text="WSL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(env_frame, textvariable=self.wsl_status_var).grid(row=0, column=1, sticky=tk.W, pady=2, padx=10)
        
        # Podman 状态
        self.podman_status_var = tk.StringVar(value="检查中...")
        ttk.Label(env_frame, text="Podman:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(env_frame, textvariable=self.podman_status_var).grid(row=1, column=1, sticky=tk.W, pady=2, padx=10)
        
        # Podman 版本
        self.podman_version_var = tk.StringVar(value="")
        ttk.Label(env_frame, text="版本:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(env_frame, textvariable=self.podman_version_var).grid(row=2, column=1, sticky=tk.W, pady=2, padx=10)
        
        # 刷新状态按钮
        refresh_btn = ttk.Button(env_frame, text="刷新状态", command=self._refresh_status)
        refresh_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        # 日志输出区域
        log_frame = ttk.LabelFrame(status_frame, text="日志输出", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始刷新状态
        self._refresh_status()
    
    def _refresh_wsl_distros(self) -> None:
        """刷新 WSL 发行版列表"""
        try:
            result = subprocess.run(
                ["wsl", "-l", "-q"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # 解析发行版列表
                distros = [
                    line.strip() 
                    for line in result.stdout.split("\n") 
                    if line.strip()
                ]
                self.wsl_distro_combo["values"] = distros
                
                # 如果当前值不在列表中，选择第一个
                if self.wsl_distro_var.get() not in distros and distros:
                    self.wsl_distro_var.set(distros[0])
                
                self._log(f"已加载 {len(distros)} 个 WSL 发行版")
            else:
                self._log("无法获取 WSL 发行版列表")
                
        except Exception as e:
            self._log(f"获取 WSL 发行版失败: {e}")
    
    def _refresh_status(self) -> None:
        """刷新环境状态"""
        # 在后台线程中检查
        def check():
            # 检查 WSL
            try:
                result = subprocess.run(
                    ["wsl", "-l", "-v"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    distro = self.wsl_distro_var.get()
                    if distro.lower() in result.stdout.lower():
                        self.wsl_status_var.set("✓ 可用")
                    else:
                        self.wsl_status_var.set("✗ 发行版未找到")
                else:
                    self.wsl_status_var.set("✗ 不可用")
            except Exception:
                self.wsl_status_var.set("✗ 不可用")
            
            # 检查 Podman
            try:
                result = subprocess.run(
                    ["wsl", "-d", self.wsl_distro_var.get(), "--", "podman", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    self.podman_status_var.set("✓ 可用")
                    self.podman_version_var.set(result.stdout.strip())
                else:
                    self.podman_status_var.set("✗ 不可用")
                    self.podman_version_var.set("")
            except Exception:
                self.podman_status_var.set("✗ 不可用")
                self.podman_version_var.set("")
        
        threading.Thread(target=check, daemon=True).start()
    
    def _test_path_conversion(self) -> None:
        """测试路径转换"""
        from .path_converter import PathConverter
        
        # 使用当前设置创建临时配置
        temp_config = Config()
        temp_config.windows_drives_prefix = self.drives_prefix_var.get()
        
        converter = PathConverter(temp_config)
        windows_path = self.test_input_var.get()
        
        try:
            wsl_path = converter.windows_to_wsl(windows_path)
            self.test_output_var.set(wsl_path)
            self._log(f"路径转换: {windows_path} -> {wsl_path}")
        except Exception as e:
            self.test_output_var.set(f"错误: {e}")
            self._log(f"路径转换失败: {e}")
    
    def _save_config(self) -> None:
        """保存配置"""
        try:
            # 更新配置值
            self.config.wsl_distro = self.wsl_distro_var.get()
            self.config.podman_path = self.podman_path_var.get()
            self.config.command_timeout = int(self.timeout_var.get())
            self.config.stream_buffer_size = int(self.buffer_var.get())
            self.config.windows_drives_prefix = self.drives_prefix_var.get()
            self.config.mount_point = self.mount_point_var.get()
            
            # 保存到文件
            self.config.save()
            
            self.status_var.set("配置已保存")
            self._log("配置已保存")
            messagebox.showinfo("成功", "配置已保存！")
            
        except ValueError as e:
            messagebox.showerror("错误", f"输入值无效: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def _reset_config(self) -> None:
        """重置为默认配置"""
        if messagebox.askyesno("确认", "确定要重置为默认配置吗？"):
            # 重置配置对象
            self.config = Config()
            
            # 更新界面
            self.wsl_distro_var.set(self.config.wsl_distro)
            self.podman_path_var.set(self.config.podman_path)
            self.timeout_var.set(str(self.config.command_timeout))
            self.buffer_var.set(str(self.config.stream_buffer_size))
            self.drives_prefix_var.set(self.config.windows_drives_prefix)
            self.mount_point_var.set(self.config.mount_point)
            
            self.status_var.set("已重置为默认配置")
            self._log("配置已重置为默认值")
    
    def _check_environment(self) -> None:
        """检查环境"""
        self._log("开始检查环境...")
        self._refresh_status()
        
        # 在后台线程中执行检查
        def check():
            from .proxy import DockerProxy
            
            proxy = DockerProxy(self.config)
            
            wsl_ok = proxy.check_wsl_available()
            podman_ok = proxy.check_podman_available()
            
            if wsl_ok and podman_ok:
                self.root.after(0, lambda: messagebox.showinfo("检查结果", "环境检查通过！\nWSL 和 Podman 均可用。"))
            else:
                msg = "环境检查发现问题:\n"
                if not wsl_ok:
                    msg += "- WSL 不可用或发行版未找到\n"
                if not podman_ok:
                    msg += "- Podman 不可用\n"
                self.root.after(0, lambda: messagebox.showwarning("检查结果", msg))
            
            self._log("环境检查完成")
        
        threading.Thread(target=check, daemon=True).start()
    
    def _set_icon(self) -> None:
        """设置窗口图标"""
        import os
        
        # 图标文件路径（与 gui.py 同目录）
        icon_path = os.path.join(os.path.dirname(__file__), "foxker.ico")
        
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(default=icon_path)
            except tk.TclError:
                pass  # 静默忽略图标加载失败
    
    def _log(self, message: str) -> None:
        """添加日志消息"""
        # 如果 log_text 还未创建，直接返回（静默处理）
        if self.log_text is None:
            return
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
    
    def run(self) -> None:
        """运行 GUI"""
        self.root.mainloop()


def launch_gui() -> None:
    """启动 GUI（用于命令行入口）"""
    app = FoxkerGUI()
    app.run()


if __name__ == "__main__":
    launch_gui()
