"""
配置管理模块
负责加载和管理配置文件
"""

import yaml
from pathlib import Path
import click
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        'api': {
            'openai_key': ''
        },
        'voice': {
            'default': 'alloy',
            'speed': 1.0,
            'model': 'tts-1-hd'
        },
        'output': {
            'format': 'mp3',
            'bitrate': '128k',
            'directory': './'
        },
        'processing': {
            'max_retries': 3,
            'timeout': 30,
            'concurrent': 3,
            'text_rules': {
                'normalize_punctuation': True,
                'convert_numbers': False
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 自定义配置文件路径
        """
        # 加载默认配置
        self.config = self._deep_copy(self.DEFAULT_CONFIG)
        
        # 加载用户全局配置
        self._load_user_config()
        
        # 加载指定的配置文件
        if config_path:
            self._load_file(config_path)
    
    def _deep_copy(self, obj: Dict) -> Dict:
        """深拷贝配置字典"""
        import copy
        return copy.deepcopy(obj)
    
    def _merge_config(self, source: Dict, target: Dict):
        """
        递归合并配置
        
        Args:
            source: 源配置
            target: 目标配置（会被修改）
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(value, target[key])
            else:
                target[key] = value
    
    def _load_user_config(self):
        """加载用户全局配置"""
        config_file = Path.home() / '.srt2voice' / 'config.yaml'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                    self._merge_config(user_config, self.config)
            except Exception as e:
                print(f"警告: 加载用户配置失败: {e}")
    
    def _load_file(self, config_path: str):
        """加载指定的配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                custom_config = yaml.safe_load(f) or {}
                self._merge_config(custom_config, self.config)
        except Exception as e:
            raise ValueError(f"配置文件解析失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的路径 (如 'api.openai_key')
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的路径
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_to_file(self, file_path: str):
        """保存配置到文件"""
        output_file = Path(file_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    @staticmethod
    def setup_config():
        """配置向导"""
        click.echo("=== SRT2Voice 配置向导 ===")
        click.echo("")
        
        # 获取API密钥
        api_key = click.prompt("请输入您的OpenAI API密钥", hide_input=True)
        
        # 选择默认语音
        click.echo("\n可用的语音类型:")
        voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        for i, voice in enumerate(voices, 1):
            click.echo(f"  {i}. {voice}")
        
        voice_choice = click.prompt("选择默认语音 (1-6)", type=int, default=1)
        default_voice = voices[voice_choice - 1] if 1 <= voice_choice <= 6 else "alloy"
        
        # 创建配置
        config_dir = Path.home() / '.srt2voice'
        config_dir.mkdir(exist_ok=True)
        
        config_data = ConfigManager.DEFAULT_CONFIG.copy()
        config_data['api']['openai_key'] = api_key
        config_data['voice']['default'] = default_voice
        
        # 保存配置
        config_file = config_dir / 'config.yaml'
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        click.echo(f"\n配置已保存到: {config_file}")
        click.echo("您可以随时编辑此文件来修改配置")
        
        return config_file