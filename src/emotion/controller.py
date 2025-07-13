"""情感控制器模块"""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class EmotionController:
    """情感控制器基类，管理情感到TTS参数的映射"""
    
    # 默认情感预设
    DEFAULT_EMOTIONS = {
        "neutral": {
            "name": "中性",
            "description": "平稳、清晰的播音风格"
        },
        "emphasis": {
            "name": "强调",
            "description": "更加稳重、严肃的语调"
        },
        "friendly": {
            "name": "友好",
            "description": "活泼、亲切的语调"
        },
        "professional": {
            "name": "专业",
            "description": "正式、商务的语调"
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """初始化情感控制器
        
        Args:
            config_path: 情感配置文件路径
        """
        self.emotion_mappings = {}
        self.custom_emotions = {}
        
        # 加载情感配置
        if config_path and config_path.exists():
            self.load_emotion_config(config_path)
        else:
            logger.info("未找到情感配置文件，使用默认设置")
    
    def load_emotion_config(self, config_path: Path) -> None:
        """加载情感配置文件
        
        Args:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 加载自定义情感
            if 'emotions' in config:
                self.custom_emotions = config['emotions']
                logger.info(f"加载了 {len(self.custom_emotions)} 个自定义情感")
            
            # 加载服务特定的映射
            if 'service_mappings' in config:
                self.emotion_mappings = config['service_mappings']
                logger.info("加载了服务特定的情感映射")
                
        except Exception as e:
            logger.error(f"加载情感配置失败: {e}")
    
    def get_available_emotions(self) -> List[str]:
        """获取所有可用的情感类型
        
        Returns:
            List[str]: 可用情感类型列表
        """
        emotions = list(self.DEFAULT_EMOTIONS.keys())
        emotions.extend(self.custom_emotions.keys())
        return list(set(emotions))  # 去重
    
    def get_emotion_info(self, emotion: str) -> Dict[str, Any]:
        """获取情感信息
        
        Args:
            emotion: 情感类型
            
        Returns:
            Dict: 情感信息
        """
        # 先查找自定义情感
        if emotion in self.custom_emotions:
            return self.custom_emotions[emotion]
        
        # 再查找默认情感
        if emotion in self.DEFAULT_EMOTIONS:
            return self.DEFAULT_EMOTIONS[emotion]
        
        # 未找到，返回中性
        logger.warning(f"未知的情感类型: {emotion}，使用中性")
        return self.DEFAULT_EMOTIONS["neutral"]
    
    def get_service_parameters(self, emotion: str, service_name: str) -> Dict[str, Any]:
        """获取特定服务的情感参数
        
        Args:
            emotion: 情感类型
            service_name: 服务名称
            
        Returns:
            Dict: TTS参数
        """
        # 如果有服务特定的映射，优先使用
        if service_name in self.emotion_mappings:
            service_mappings = self.emotion_mappings[service_name]
            if emotion in service_mappings:
                return service_mappings[emotion]
        
        # 否则使用默认映射
        return self._get_default_mapping(emotion, service_name)
    
    def _get_default_mapping(self, emotion: str, service_name: str) -> Dict[str, Any]:
        """获取默认的情感参数映射
        
        Args:
            emotion: 情感类型
            service_name: 服务名称
            
        Returns:
            Dict: TTS参数
        """
        if service_name == "gpt_sovits":
            return self._get_gptsovits_mapping(emotion)
        elif service_name == "gemini":
            return self._get_gemini_mapping(emotion)
        else:
            logger.warning(f"未知的服务: {service_name}")
            return {}
    
    def _get_gptsovits_mapping(self, emotion: str) -> Dict[str, Any]:
        """获取GPT-SoVITS的情感参数映射
        
        Args:
            emotion: 情感类型
            
        Returns:
            Dict: GPT-SoVITS参数
        """
        mappings = {
            "neutral": {
                "temperature": 0.3,
                "top_k": 3,
                "top_p": 0.7,
                "speed_factor": 1.0
            },
            "emphasis": {
                "temperature": 0.2,  # 更稳定
                "top_k": 2,         # 更保守
                "top_p": 0.5,
                "speed_factor": 0.9  # 稍慢
            },
            "friendly": {
                "temperature": 0.5,  # 更活泼
                "top_k": 5,         # 更多变化
                "top_p": 0.9,
                "speed_factor": 1.1  # 稍快
            },
            "professional": {
                "temperature": 0.25,
                "top_k": 3,
                "top_p": 0.6,
                "speed_factor": 0.95
            }
        }
        
        return mappings.get(emotion, mappings["neutral"])
    
    def _get_gemini_mapping(self, emotion: str) -> Dict[str, Any]:
        """获取Gemini的情感参数映射
        
        Args:
            emotion: 情感类型
            
        Returns:
            Dict: Gemini参数
        """
        # Gemini主要通过选择不同的voice_name来实现情感变化
        voice_mappings = {
            "neutral": {"voice_name": "Kore"},      # 清晰的标准声音
            "emphasis": {"voice_name": "Charon"},    # 更深沉严肃
            "friendly": {"voice_name": "Puck"},      # 更活泼友好
            "professional": {"voice_name": "Vale"}   # 专业正式
        }
        
        return voice_mappings.get(emotion, voice_mappings["neutral"])
    
    def apply_emotion_to_config(self, emotion: str, service_name: str, 
                               base_config: Dict[str, Any]) -> Dict[str, Any]:
        """将情感参数应用到基础配置
        
        Args:
            emotion: 情感类型
            service_name: 服务名称
            base_config: 基础配置
            
        Returns:
            Dict: 更新后的配置
        """
        # 获取情感参数
        emotion_params = self.get_service_parameters(emotion, service_name)
        
        # 深拷贝基础配置
        import copy
        config = copy.deepcopy(base_config)
        
        # 更新voice_settings
        if 'voice_settings' not in config:
            config['voice_settings'] = {}
        
        config['voice_settings'].update(emotion_params)
        
        logger.info(f"应用情感 '{emotion}' 到服务 '{service_name}'")
        logger.debug(f"情感参数: {emotion_params}")
        
        return config


class EmotionSequence:
    """情感序列管理器，支持按字幕索引或时间轴设置不同情感"""
    
    def __init__(self):
        """初始化情感序列"""
        self.emotion_map = {}  # {subtitle_index: emotion}
        self.default_emotion = "neutral"
    
    def set_emotion(self, index: int, emotion: str) -> None:
        """为特定字幕设置情感
        
        Args:
            index: 字幕索引
            emotion: 情感类型
        """
        self.emotion_map[index] = emotion
    
    def set_emotion_range(self, start: int, end: int, emotion: str) -> None:
        """为字幕范围设置情感
        
        Args:
            start: 开始索引
            end: 结束索引（包含）
            emotion: 情感类型
        """
        for i in range(start, end + 1):
            self.emotion_map[i] = emotion
    
    def get_emotion(self, index: int) -> str:
        """获取指定字幕的情感
        
        Args:
            index: 字幕索引
            
        Returns:
            str: 情感类型
        """
        return self.emotion_map.get(index, self.default_emotion)
    
    def load_from_file(self, file_path: Path) -> None:
        """从文件加载情感序列
        
        Args:
            file_path: 情感序列文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if 'default' in data:
                self.default_emotion = data['default']
            
            if 'sequence' in data:
                for item in data['sequence']:
                    if 'range' in item:
                        start, end = item['range']
                        self.set_emotion_range(start, end, item['emotion'])
                    elif 'index' in item:
                        self.set_emotion(item['index'], item['emotion'])
            
            logger.info(f"加载了情感序列，包含 {len(self.emotion_map)} 个特定设置")
            
        except Exception as e:
            logger.error(f"加载情感序列失败: {e}")