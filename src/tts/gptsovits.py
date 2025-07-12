"""GPT-SoVITS TTS服务实现"""
import io
import logging
import time
import signal
from typing import Dict, Any, Optional
import requests
from pydub import AudioSegment
from rich.console import Console
from .base import TTSService
from ..utils.gpt_sovits_manager import GPTSoVITSManager


logger = logging.getLogger('srt2speech.gptsovits')

# 全局集合，跟踪所有活动的服务实例
_active_services = set()


def _signal_handler(signum, frame):
    """信号处理器，确保所有服务被正确清理"""
    # 延迟一下，让CLI先输出消息
    import time
    time.sleep(0.1)
    
    # 创建服务列表的副本，避免在迭代时修改集合
    services_to_cleanup = list(_active_services)
    if services_to_cleanup:
        for service in services_to_cleanup:
            if hasattr(service, '_cleanup'):
                service._cleanup()


# 注册信号处理器
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


class GPTSoVITSService(TTSService):
    """GPT-SoVITS本地TTS服务"""
    
    def __init__(self, config: dict):
        """初始化GPT-SoVITS服务
        
        Args:
            config: 服务配置字典
        """
        # 先初始化必要的属性，供validate_config使用
        self.api_url = config['credentials']['api_url']
        self.api_version = config['credentials'].get('api_version', 'v2')
        self.voice_settings = config['voice_settings']
        
        # 设置默认超时时间
        self.timeout = 30
        self.max_retries = 3
        
        # 标记服务是否被手动停止
        self._manually_stopped = False
        
        # 添加调试日志
        logger.debug(f"Creating GPTSoVITSService instance: {id(self)}")
        
        # 初始化服务管理器
        self.service_manager = None
        auto_start_config = config.get('auto_start', {})
        logger.debug(f"Auto-start config: {auto_start_config}")
        if auto_start_config.get('enabled', False):
            logger.info("✅ GPT-SoVITS 自动启动已启用")
            self.service_manager = GPTSoVITSManager(auto_start_config, api_version=self.api_version)
            # 不再注册atexit，依靠信号处理器和_active_services集合管理生命周期
        else:
            logger.debug("自动启动未启用或未配置")
        
        # 调用父类初始化，会触发validate_config
        super().__init__(config)
        
        # 将实例添加到活动服务集合中
        _active_services.add(self)
        logger.debug(f"Added instance {id(self)} to _active_services, total: {len(_active_services)}")
        
        logger.info(f"初始化GPT-SoVITS服务，API地址：{self.api_url}，版本：{self.api_version}")
    
    def __del__(self):
        """析构函数，用于调试"""
        logger.debug(f"GPTSoVITSService instance {id(self)} is being destroyed")
        if hasattr(self, 'service_manager') and self.service_manager:
            logger.warning(f"Instance {id(self)} being destroyed with active service_manager!")
    
    def validate_config(self) -> None:
        """验证配置有效性"""
        required_fields = ['api_url']
        for field in required_fields:
            if field not in self.config['credentials']:
                raise ValueError(f"缺少必需的配置项：credentials.{field}")
        
        # 如果使用voice_profile，这些字段可能在profile中定义
        # 先检查是否所有必需字段都存在
        required_voice_fields = ['language', 'ref_audio_path', 'prompt_text', 'prompt_lang']
        missing_fields = [field for field in required_voice_fields if field not in self.voice_settings]
        
        if missing_fields:
            # 如果有缺失字段，但配置了voice_profile，给出更清晰的错误信息
            if 'voice_profile' in self.voice_settings:
                raise ValueError(f"voice_profile配置可能有问题，缺少必需字段：{', '.join(missing_fields)}")
            else:
                raise ValueError(f"缺少必需的配置项：voice_settings.{missing_fields[0]}")
        
        # 尝试自动启动服务（如果配置了）
        if self.service_manager and not self.check_health():
            console = Console()
            console.print("[yellow]🔍 GPT-SoVITS服务未运行，正在自动启动...[/yellow]")
            if not self.service_manager.start_service(self.api_url):
                raise ConnectionError(f"无法自动启动GPT-SoVITS服务")
            console.print("[green]✅ GPT-SoVITS API 服务已成功启动！[/green]")
        
        # 验证服务连接
        if not self.check_health():
            raise ConnectionError(f"无法连接到GPT-SoVITS服务：{self.api_url}")
    
    def check_health(self) -> bool:
        """检查服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        try:
            response = requests.get(
                f"{self.api_url}/", 
                timeout=5
            )
            return response.status_code < 500
        except Exception as e:
            logger.debug(f"GPT-SoVITS服务健康检查失败：{e}")
            return False
    
    def text_to_speech(self, text: str) -> AudioSegment:
        """将文本转换为语音
        
        Args:
            text: 要转换的文本
            
        Returns:
            AudioSegment: 音频片段
        """
        if not text.strip():
            # 返回静音片段
            return AudioSegment.silent(duration=100)
        
        # 根据API版本选择不同的请求方式
        if self.api_version == 'v2':
            return self._tts_v2(text)
        else:
            return self._tts_v1(text)
    
    def _tts_v1(self, text: str) -> AudioSegment:
        """使用API v1进行TTS"""
        url = self.api_url
        params = {
            "text": text,
            "text_language": self.voice_settings['language'],
            "refer_wav_path": self.voice_settings['ref_audio_path'],
            "prompt_text": self.voice_settings['prompt_text'],
            "prompt_language": self.voice_settings['prompt_lang']
        }
        
        # 添加可选参数
        optional_params = ['top_k', 'top_p', 'temperature', 'speed']
        for param in optional_params:
            if param in self.voice_settings:
                params[param] = self.voice_settings[param]
        
        return self._make_request('GET', url, params=params)
    
    def _tts_v2(self, text: str) -> AudioSegment:
        """使用API v2进行TTS"""
        url = f"{self.api_url}/tts"
        data = {
            "text": text,
            "text_lang": self.voice_settings['language'],
            "ref_audio_path": self.voice_settings['ref_audio_path'],
            "prompt_text": self.voice_settings['prompt_text'],
            "prompt_lang": self.voice_settings['prompt_lang']
        }
        
        # 添加所有其他配置的参数
        v2_params = [
            'aux_ref_audio_paths', 'top_k', 'top_p', 'temperature',
            'text_split_method', 'batch_size', 'batch_threshold',
            'split_bucket', 'speed_factor', 'fragment_interval',
            'seed', 'media_type', 'streaming_mode', 'parallel_infer',
            'repetition_penalty', 'sample_steps', 'super_sampling'
        ]
        
        for param in v2_params:
            if param in self.voice_settings:
                data[param] = self.voice_settings[param]
        
        return self._make_request('POST', url, json=data)
    
    def _make_request(self, method: str, url: str, **kwargs) -> AudioSegment:
        """发送HTTP请求并处理响应"""
        for attempt in range(self.max_retries):
            # 如果服务已被手动停止，立即退出
            if self._manually_stopped:
                raise Exception("GPT-SoVITS服务已被停止")
            
            try:
                if method == 'GET':
                    response = requests.get(url, timeout=self.timeout, **kwargs)
                else:
                    response = requests.post(url, timeout=self.timeout, **kwargs)
                
                if response.status_code == 200:
                    # 处理流式响应
                    if self.voice_settings.get('streaming_mode', False):
                        audio_data = io.BytesIO()
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                audio_data.write(chunk)
                        audio_data.seek(0)
                    else:
                        audio_data = io.BytesIO(response.content)
                    
                    # 根据媒体类型处理音频
                    media_type = self.voice_settings.get('media_type', 'wav')
                    if media_type == 'wav':
                        return AudioSegment.from_wav(audio_data)
                    elif media_type == 'ogg':
                        return AudioSegment.from_ogg(audio_data)
                    elif media_type == 'aac':
                        return AudioSegment.from_file(audio_data, format='aac')
                    else:
                        return AudioSegment.from_file(audio_data)
                
                else:
                    error_msg = f"TTS请求失败，状态码：{response.status_code}"
                    try:
                        error_detail = response.json()
                        error_msg += f"，错误详情：{error_detail}"
                    except:
                        error_msg += f"，响应内容：{response.text[:200]}"
                    
                    if attempt < self.max_retries - 1:
                        logger.warning(f"{error_msg}，正在重试...")
                        time.sleep(1)
                        continue
                    else:
                        raise Exception(error_msg)
                        
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    logger.warning(f"请求超时，正在重试 ({attempt + 1}/{self.max_retries})...")
                    time.sleep(1)
                    continue
                else:
                    raise Exception("TTS请求超时")
                    
            except requests.exceptions.ConnectionError:
                # 检查是否有服务被手动停止
                if any(hasattr(s, '_manually_stopped') and s._manually_stopped for s in _active_services):
                    raise Exception("GPT-SoVITS服务已被停止")
                
                if attempt < self.max_retries - 1:
                    logger.warning(f"连接失败，正在重试 ({attempt + 1}/{self.max_retries})...")
                    time.sleep(2)
                    continue
                else:
                    raise Exception(f"无法连接到GPT-SoVITS服务：{self.api_url}")
                    
            except Exception as e:
                if "CUDA out of memory" in str(e) and attempt < self.max_retries - 1:
                    # GPU内存不足，尝试降低batch_size
                    logger.warning("GPU内存不足，降低batch_size后重试...")
                    self.voice_settings['batch_size'] = 1
                    time.sleep(2)
                    continue
                else:
                    raise
    
    def switch_model(self, model_type: str, model_path: str) -> bool:
        """切换模型（仅v2版本支持）
        
        Args:
            model_type: 模型类型（'gpt' 或 'sovits'）
            model_path: 模型文件路径
            
        Returns:
            bool: 是否切换成功
        """
        if self.api_version != 'v2':
            logger.warning("模型切换仅在API v2版本中支持")
            return False
        
        if model_type == 'gpt':
            url = f"{self.api_url}/set_gpt_weights"
        elif model_type == 'sovits':
            url = f"{self.api_url}/set_sovits_weights"
        else:
            raise ValueError(f"不支持的模型类型：{model_type}")
        
        try:
            response = requests.get(
                url,
                params={"weights_path": model_path},
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"成功切换{model_type}模型：{model_path}")
                return True
            else:
                logger.error(f"切换模型失败：{response.text}")
                return False
        except Exception as e:
            logger.error(f"切换模型时发生错误：{e}")
            return False
    
    def _cleanup(self) -> None:
        """清理资源，停止自动启动的服务"""
        logger.debug(f"_cleanup called for instance {id(self)}, stack trace:")
        import traceback
        logger.debug(''.join(traceback.format_stack()))
        
        self._manually_stopped = True
        
        if self.service_manager:
            try:
                self.service_manager.stop_service()
                self.service_manager = None  # 防止重复清理
            except Exception as e:
                logger.error(f"清理服务时发生错误：{e}")
        
        # 从活动服务集合中移除
        _active_services.discard(self)
        logger.debug(f"Removed instance {id(self)} from _active_services, remaining: {len(_active_services)}")