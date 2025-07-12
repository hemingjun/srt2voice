"""GPT-SoVITS 服务管理器"""
import os
import time
import logging
import subprocess
import signal
import requests
from pathlib import Path
from typing import Optional
from rich.console import Console


logger = logging.getLogger('srt2speech.gpt_sovits_manager')


class GPTSoVITSManager:
    """GPT-SoVITS 服务管理器"""
    
    def __init__(self, config: dict, api_version: str = 'v2'):
        """初始化服务管理器
        
        Args:
            config: auto_start 配置字典
            api_version: API版本 ('v1' 或 'v2')
        """
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.gpt_sovits_path = Path(config.get('gpt_sovits_path', ''))
        self.startup_timeout = config.get('startup_timeout', 30)
        self.use_command_script = config.get('use_command_script', True)
        self.api_version = api_version
        self.api_url = None  # 将在启动时设置
        
    def is_service_running(self, api_url: str) -> bool:
        """检查服务是否正在运行
        
        Args:
            api_url: API服务地址
            
        Returns:
            bool: 服务是否在运行
        """
        try:
            response = requests.get(f"{api_url}/", timeout=2)
            return response.status_code < 500
        except:
            return False
            
    def start_service(self, api_url: str) -> bool:
        """启动 GPT-SoVITS 服务
        
        Args:
            api_url: API服务地址
            
        Returns:
            bool: 启动是否成功
        """
        self.api_url = api_url
        
        # 检查服务是否已经在运行
        if self.is_service_running(api_url):
            logger.info("GPT-SoVITS 服务已在运行")
            return True
            
        # 验证路径
        if not self.gpt_sovits_path.exists():
            logger.error(f"GPT-SoVITS 路径不存在：{self.gpt_sovits_path}")
            return False
            
        # 选择启动方式
        if self.use_command_script:
            return self._start_with_command_script()
        else:
            return self._start_with_python()
            
    def _start_with_command_script(self) -> bool:
        """使用 go-api.command 脚本启动服务"""
        # 对于v2版本，没有专门的脚本，直接使用Python启动
        if self.api_version == "v2":
            logger.info("API v2 没有专用启动脚本，使用 Python 直接启动")
            return self._start_with_python()
            
        script_path = self.gpt_sovits_path / "go-api.command"
        
        if not script_path.exists():
            logger.warning("go-api.command 不存在，尝试使用 Python 直接启动")
            return self._start_with_python()
            
        try:
            logger.info(f"使用脚本启动 GPT-SoVITS：{script_path}")
            
            # 确保脚本有执行权限
            os.chmod(script_path, 0o755)
            
            # 启动进程（让输出显示在终端，避免阻塞）
            logger.info("🚀 正在启动 GPT-SoVITS API 服务...")
            self.process = subprocess.Popen(
                [str(script_path)],
                cwd=str(self.gpt_sovits_path),
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            return self._wait_for_service()
            
        except Exception as e:
            logger.error(f"启动 GPT-SoVITS 失败：{e}")
            return False
            
    def _start_with_python(self) -> bool:
        """直接使用 Python 启动服务"""
        try:
            logger.info(f"使用 Python 直接启动 GPT-SoVITS (API {self.api_version})")
            
            # 构建启动命令
            runtime_python = self.gpt_sovits_path / "runtime" / "bin" / "python3"
            if runtime_python.exists():
                python_cmd = str(runtime_python)
            else:
                python_cmd = "python"
            
            # 根据API版本选择正确的脚本
            api_script = "api_v2.py" if self.api_version == "v2" else "api.py"
            
            cmd = [
                python_cmd,
                api_script,
                "-a", "127.0.0.1",
                "-p", "9880"
            ]
            
            # 如果是v2版本，添加配置文件参数
            if self.api_version == "v2":
                cmd.extend(["-c", "GPT_SoVITS/configs/tts_infer.yaml"])
            
            # 启动进程（将输出重定向到空设备，避免阻塞）
            logger.info(f"🚀 正在启动 GPT-SoVITS API 服务 ({api_script})...")
            self.process = subprocess.Popen(
                cmd,
                cwd=str(self.gpt_sovits_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            return self._wait_for_service()
            
        except Exception as e:
            logger.error(f"启动 GPT-SoVITS 失败：{e}")
            return False
            
    def _wait_for_service(self) -> bool:
        """等待服务启动完成
        
        Returns:
            bool: 服务是否成功启动
        """
        console = Console()
        console.print(f"[cyan]⏳ 等待 GPT-SoVITS 服务启动（超时：{self.startup_timeout}秒）...[/cyan]")
        
        start_time = time.time()
        check_count = 0
        while time.time() - start_time < self.startup_timeout:
            # 检查进程是否还在运行
            if self.process.poll() is not None:
                console.print("[red]❌ GPT-SoVITS 进程意外退出[/red]")
                return False
                
            # 检查服务是否可用
            if self.is_service_running(self.api_url):
                console.print(f"[green]✅ GPT-SoVITS API 服务已启动成功！[/green]")
                console.print(f"[green]   📍 服务地址：{self.api_url}[/green]")
                console.print(f"[green]   🔖 API版本：{self.api_version}[/green]")
                return True
            
            check_count += 1
            if check_count % 5 == 0:
                console.print(f"[dim]   等待中... ({check_count}秒)[/dim]")
            time.sleep(1)
            
        logger.error(f"GPT-SoVITS 服务启动超时（{self.startup_timeout}秒）")
        self.stop_service()
        return False
        
    def stop_service(self) -> None:
        """停止 GPT-SoVITS 服务"""
        if not self.process:
            return
            
        if self.process.poll() is not None:
            # 进程已经结束
            self.process = None
            return
            
        logger.info("🛑 正在关闭 GPT-SoVITS API 服务...")
        
        try:
            # 首先尝试优雅关闭
            if os.name != 'nt':
                # Unix/Linux/macOS: 向进程组发送信号
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    logger.warning("进程组不存在，尝试直接终止进程")
                    self.process.terminate()
            else:
                # Windows
                self.process.terminate()
                
            # 等待进程结束
            try:
                self.process.wait(timeout=5)
                logger.info("✅ GPT-SoVITS API 服务已完全关闭")
            except subprocess.TimeoutExpired:
                logger.warning("正常停止超时，强制终止进程")
                if os.name != 'nt':
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    except:
                        self.process.kill()
                else:
                    self.process.kill()
                self.process.wait(timeout=2)
                
        except Exception as e:
            logger.error(f"停止服务时发生错误：{e}")
            # 最后的尝试
            try:
                self.process.kill()
            except:
                pass
                
        finally:
            self.process = None
            
            # 验证端口是否已释放
            if self.api_url:
                time.sleep(0.5)  # 给系统一点时间释放端口
                if self.is_service_running(self.api_url):
                    logger.warning("服务停止后端口仍被占用")