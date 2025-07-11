import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

load_dotenv()


class VoiceSettings(BaseModel):
    language: str = Field(default="zh-CN", description="Language code")
    gender: str = Field(default="FEMALE", description="Voice gender")
    name: Optional[str] = Field(default=None, description="Specific voice name")
    speaking_rate: float = Field(default=1.0, ge=0.25, le=4.0, description="Speaking rate")
    pitch: float = Field(default=0.0, ge=-20.0, le=20.0, description="Voice pitch")
    volume_gain_db: float = Field(default=0.0, ge=-96.0, le=16.0, description="Volume gain in dB")


class ServiceConfig(BaseModel):
    service_name: str = Field(description="TTS service name")
    priority: int = Field(default=1, ge=1, description="Service priority (lower is higher priority)")
    enabled: bool = Field(default=True, description="Whether the service is enabled")
    credentials: Dict[str, str] = Field(default_factory=dict, description="Service credentials")
    voice_settings: VoiceSettings = Field(default_factory=VoiceSettings, description="Voice settings")
    
    @validator('credentials')
    def validate_credentials(cls, v, values):
        service_name = values.get('service_name')
        if not v and service_name:
            # Try to load from environment variables
            if service_name == 'google':
                key_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if key_file:
                    v['key_file'] = key_file
            elif service_name == 'azure':
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
        'crossfade_duration': 0.01
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
        self.config_path = Path(config_path) if config_path else Path('config/default.yaml')
        self.config = self._load_config()
    
    def _load_config(self) -> Config:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            return Config(**data)
        else:
            # Return default config if file doesn't exist
            return Config()
    
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