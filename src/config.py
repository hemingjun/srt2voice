import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

load_dotenv()


class VoiceSettings(BaseModel):
    language: str = Field(default="zh-CN", description="Language code")
    gender: Optional[str] = Field(default="FEMALE", description="Voice gender")
    name: Optional[str] = Field(default=None, description="Specific voice name")
    speaking_rate: float = Field(default=1.0, ge=0.25, le=4.0, description="Speaking rate")
    pitch: float = Field(default=0.0, ge=-20.0, le=20.0, description="Voice pitch")
    volume_gain_db: float = Field(default=0.0, ge=-96.0, le=16.0, description="Volume gain in dB")
    
    # GPT-SoVITS specific fields
    ref_audio_path: Optional[str] = Field(default=None, description="Reference audio path")
    prompt_text: Optional[str] = Field(default=None, description="Reference audio text")
    prompt_lang: Optional[str] = Field(default=None, description="Reference audio language")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Top-K sampling")
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1, description="Top-P sampling")
    temperature: Optional[float] = Field(default=1.0, ge=0, le=2, description="Temperature")
    speed_factor: Optional[float] = Field(default=1.0, ge=0.5, le=2.0, description="Speed factor")
    text_split_method: Optional[str] = Field(default="cut5", description="Text split method")
    batch_size: Optional[int] = Field(default=1, ge=1, description="Batch size")
    media_type: Optional[str] = Field(default="wav", description="Media type")
    streaming_mode: Optional[bool] = Field(default=False, description="Streaming mode")
    
    # Gemini TTS specific fields
    model: Optional[str] = Field(default=None, description="Gemini model name")
    voice_name: Optional[str] = Field(default=None, description="Gemini voice name")
    
    # Allow extra fields for flexibility
    class Config:
        extra = "allow"


class ServiceConfig(BaseModel):
    service_name: str = Field(description="TTS service name")
    priority: int = Field(default=1, ge=1, description="Service priority (lower is higher priority)")
    enabled: bool = Field(default=True, description="Whether the service is enabled")
    credentials: Dict[str, str] = Field(default_factory=dict, description="Service credentials")
    voice_settings: VoiceSettings = Field(default_factory=VoiceSettings, description="Voice settings")
    auto_start: Optional[Dict[str, Any]] = Field(default=None, description="Auto-start configuration for services")
    connection: Optional[Dict[str, Any]] = Field(default=None, description="Connection configuration")
    retry_strategy: Optional[Dict[str, Any]] = Field(default=None, description="Retry strategy configuration")
    runtime: Optional[Dict[str, Any]] = Field(default=None, description="Runtime configuration")
    audio: Optional[Dict[str, Any]] = Field(default=None, description="Audio processing configuration")
    
    @validator('credentials')
    def validate_credentials(cls, v, values):
        service_name = values.get('service_name')
        if not v and service_name:
            # Try to load from environment variables
            if service_name == 'azure':
                v['subscription_key'] = os.getenv('AZURE_SPEECH_KEY', '')
                v['region'] = os.getenv('AZURE_SPEECH_REGION', 'eastus')
        return v


class Config(BaseModel):
    services: Dict[str, ServiceConfig] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=lambda: {
        'format': 'wav',
        'sample_rate': 44100,
        'channels': 1
    })
    audio_processing: Dict[str, Any] = Field(default_factory=lambda: {
        'normalize': True,
        'remove_silence': False,
        'crossfade_duration': 0.01,
        'overlap_handling': 'speed_adjust',  # Options: 'speed_adjust', 'truncate', 'warn_only'
        'speed_adjust_limit': 1.5,  # Maximum speed adjustment factor
        'fade_duration': 0.05  # Fade duration in seconds for truncation
    })
    cache: Dict[str, Any] = Field(default_factory=lambda: {
        'enabled': True,
        'directory': 'cache',
        'max_size_mb': 1000
    })
    logging: Dict[str, Any] = Field(default_factory=lambda: {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': None
    })


class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 尝试多个位置查找配置文件
            possible_paths = [
                Path('config/default.yaml'),  # 当前目录
                Path(__file__).parent.parent / 'config' / 'default.yaml',  # 相对于源码的位置
                Path.home() / '.config' / 'srt2speech' / 'default.yaml',  # 用户配置目录
            ]
            
            for path in possible_paths:
                if path.exists():
                    self.config_path = path
                    break
            else:
                # 如果都不存在，使用默认路径
                self.config_path = Path(__file__).parent.parent / 'config' / 'default.yaml'
        
        self.config = self._load_config()
    
    def _load_config(self) -> Config:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # 处理voice_profile引用
            self._process_voice_profiles(data)
            
            return Config(**data)
        else:
            # Return default config if file doesn't exist
            return Config()
    
    def _process_voice_profiles(self, data: dict) -> None:
        """处理配置中的voice_profile引用"""
        if 'services' not in data:
            return
        
        for service_name, service_config in data['services'].items():
            if not isinstance(service_config, dict):
                continue
                
            voice_settings = service_config.get('voice_settings', {})
            if not voice_settings:  # 添加None检查
                continue
                
            voice_profile = voice_settings.get('voice_profile')
            
            if voice_profile:
                # 加载voice profile配置
                profile_path = Path(f'config/reference_voices/{voice_profile}.yaml')
                if profile_path.exists():
                    try:
                        with open(profile_path, 'r', encoding='utf-8') as f:
                            profile_data = yaml.safe_load(f) or {}
                        
                        # 合并配置（profile配置优先）
                        for key in ['ref_audio_path', 'prompt_text', 'prompt_lang']:
                            if key in profile_data:
                                voice_settings[key] = profile_data[key]
                        
                        # 删除voice_profile字段，避免传递给服务
                        del voice_settings['voice_profile']
                    except Exception as e:
                        print(f"警告：加载voice profile失败 {profile_path}: {e}")
                        # 保留原始配置，但删除voice_profile避免传递给服务
                        if 'voice_profile' in voice_settings:
                            del voice_settings['voice_profile']
                else:
                    print(f"警告：找不到voice profile配置文件: {profile_path}")
                    # 删除voice_profile字段，避免传递给服务
                    if 'voice_profile' in voice_settings:
                        del voice_settings['voice_profile']
    
    def save_config(self, path: Optional[str] = None):
        """Save current configuration to YAML file."""
        save_path = Path(path) if path else self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config.dict(), f, default_flow_style=False, sort_keys=False)
    
    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get configuration for a specific service."""
        return self.config.services.get(service_name)
    
    def get_enabled_services(self) -> Dict[str, ServiceConfig]:
        """Get all enabled services sorted by priority."""
        enabled = {k: v for k, v in self.config.services.items() if v.enabled}
        return dict(sorted(enabled.items(), key=lambda x: x[1].priority))
    
    def update_service_config(self, service_name: str, updates: Dict[str, Any]):
        """Update configuration for a specific service."""
        if service_name in self.config.services:
            service_config = self.config.services[service_name].dict()
            service_config.update(updates)
            self.config.services[service_name] = ServiceConfig(**service_config)
        else:
            self.config.services[service_name] = ServiceConfig(service_name=service_name, **updates)