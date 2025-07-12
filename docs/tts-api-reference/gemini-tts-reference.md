# Google Gemini TTS 技术实现文档

## 概述

Google Gemini TTS是Google提供的先进文字转语音服务，作为Gemini API的一部分。本文档详细介绍如何将Gemini TTS集成到SRT2Speech项目中，作为第二个TTS服务选项。

**重要说明**：
1. 本文档基于新版 `google-genai` 库（非 `google-generativeai`），请确保使用正确的库版本。
2. Gemini API 可能返回 base64 编码的音频数据，我们的实现包含自动检测和解码机制。

## API特性

### 核心功能
- **多语言支持**：支持24种语言，包括中文、英文、日文、韩文等
- **多种声音**：提供多种预设声音选择（如 Kore、Vale、Journey、Puck、Charon 等）
- **自动语言检测**：可自动识别文本语言（适合中英文混合场景）
- **高质量输出**：24kHz采样率，16位深度的原始PCM音频数据

### 支持的语言列表
- 阿拉伯语 (ar)
- 中文 (cmn-CN)
- 英语 (en)
- 西班牙语 (es)
- 法语 (fr)
- 德语 (de)
- 印地语 (hi)
- 日语 (ja)
- 韩语 (ko)
- 更多语言...（共24种）

### 可用模型
- `gemini-2.5-flash-preview-tts` - 快速模型，适合实时应用
- `gemini-2.5-pro-preview-tts` - 专业模型，更高质量

## 技术实现方案

### 1. 依赖安装

```bash
pip install google-genai
```

**注意**：必须使用 `google-genai` 库，而非 `google-generativeai`。

### 2. 官方示例代码

以下是Google官方提供的使用示例：

```python
from google import genai
from google.genai import types
import wave

# 设置wave文件保存函数
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents="Say cheerfully: Have a wonderful day!",
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name='Kore',
                )
            )
        ),
    )
)

data = response.candidates[0].content.parts[0].inline_data.data
wave_file('out.wav', data)  # 保存到当前目录
```

### 3. 服务类实现

创建 `src/tts/gemini.py`：

```python
"""Google Gemini TTS服务实现"""
import io
import os
import wave
import base64
import logging
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from pydub import AudioSegment
from .base import TTSService

logger = logging.getLogger(__name__)


class GeminiTTSService(TTSService):
    """Google Gemini TTS服务
    
    使用Gemini 2.5 Flash/Pro Preview TTS模型
    支持24种语言的高质量语音合成
    """
    
    def __init__(self, config: dict):
        """初始化Gemini TTS服务
        
        Args:
            config: 服务配置字典
        """
        # 先设置必要的属性，再调用父类构造函数
        self.api_key = config['credentials'].get('api_key') or os.getenv('GEMINI_API_KEY')
        self.model_name = config['voice_settings'].get('model', 'gemini-2.5-flash-preview-tts')
        self.voice_name = config['voice_settings'].get('voice_name', 'Kore')
        
        # 初始化客户端
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"初始化Gemini TTS服务，模型：{self.model_name}，声音：{self.voice_name}")
            except Exception as e:
                logger.error(f"初始化Gemini客户端失败：{e}")
        
        # 调用父类构造函数，会触发validate_config
        super().__init__(config)
    
    def validate_config(self) -> None:
        """验证配置有效性"""
        if not self.api_key:
            raise ValueError(
                "缺少Gemini API密钥：请设置 credentials.api_key 或 GEMINI_API_KEY 环境变量"
            )
        
        if not self.client:
            raise ValueError("无法初始化Gemini客户端")
        
        # 验证模型名称
        valid_models = ['gemini-2.5-flash-preview-tts', 'gemini-2.5-pro-preview-tts']
        if self.model_name not in valid_models:
            logger.warning(
                f"模型 {self.model_name} 可能不支持TTS，推荐使用：{valid_models}"
            )
    
    def text_to_speech(self, text: str) -> AudioSegment:
        """将文本转换为语音
        
        Args:
            text: 要转换的文本
            
        Returns:
            AudioSegment: 音频片段
        """
        try:
            # 构建生成配置
            config = types.GenerateContentConfig(
                # 设置响应类型为音频
                response_modalities=["AUDIO"],
                # 配置语音参数
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice_name
                        )
                    )
                )
            )
            
            # 调用模型生成音频
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=text,
                config=config
            )
            
            # 检查响应
            if not response or not response.candidates:
                raise Exception("API未返回响应")
            
            # 从响应中提取音频数据
            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                raise Exception("响应中没有内容")
            
            # 获取音频数据
            audio_data = candidate.content.parts[0].inline_data.data
            
            # 智能检测数据格式（重要：API可能返回base64编码的数据）
            if isinstance(audio_data, str):
                # 如果是字符串，尝试base64解码
                try:
                    audio_data = base64.b64decode(audio_data)
                    logger.debug("音频数据已从base64字符串解码")
                except Exception as e:
                    logger.warning(f"Base64解码失败，尝试转换为bytes: {e}")
                    audio_data = audio_data.encode()
            elif isinstance(audio_data, bytes):
                # 检测是否可能是base64编码的bytes
                try:
                    # 尝试解码，如果成功且是有效音频数据则使用
                    decoded = base64.b64decode(audio_data, validate=True)
                    # 简单检查：PCM数据应该有一定长度
                    if len(decoded) > 1000:
                        audio_data = decoded
                        logger.debug("音频数据已从base64 bytes解码")
                except Exception:
                    # 不是base64，保持原样
                    logger.debug("音频数据是原始二进制格式")
            
            # 添加调试日志
            logger.debug(f"音频数据类型: {type(audio_data)}, 长度: {len(audio_data) if audio_data else 0}")
            
            # Gemini返回的是原始PCM数据，需要构建WAV格式
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位（2字节）
                wav_file.setframerate(24000)  # 24kHz
                wav_file.writeframes(audio_data)
            
            # 回到开始位置
            wav_buffer.seek(0)
            
            # 转换为AudioSegment
            audio = AudioSegment.from_wav(wav_buffer)
            
            # 转换为项目标准格式（32kHz）
            if audio.frame_rate != 32000:
                audio = audio.set_frame_rate(32000)
            
            logger.info(f"文本转语音成功，时长：{len(audio)/1000:.2f}秒")
            return audio
            
        except Exception as e:
            logger.error(f"Gemini TTS调用失败：{str(e)}")
            raise
    
    def check_health(self) -> bool:
        """检查服务健康状态
        
        Returns:
            bool: 服务是否可用
        """
        if not self.client:
            return False
            
        try:
            # 生成一个简短的测试音频
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice_name
                        )
                    )
                )
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents="测试",
                config=config
            )
            
            return bool(response)
            
        except Exception as e:
            logger.warning(f"Gemini服务健康检查失败：{str(e)}")
            return False
```

## API响应格式详解

### 响应结构
```python
# API响应结构
response = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "inline_data": {
                            "data": b"...",  # 原始PCM字节数据
                            "mime_type": "audio/wav"  # MIME类型标识
                        }
                    }
                ]
            }
        }
    ]
}
```

### 数据处理流程
1. **提取PCM数据**：`response.candidates[0].content.parts[0].inline_data.data`
2. **构建WAV格式**：使用Python的wave模块添加文件头
3. **格式转换**：使用pydub处理音频格式

### 3. 配置文件更新

在 `config/default.yaml` 中添加：

```yaml
  # Google Gemini TTS服务
  gemini:
    service_name: gemini
    priority: 2  # 第二优先级
    enabled: false  # 默认禁用，需要用户提供API密钥
    
    credentials:
      api_key: ""  # 可通过环境变量 GEMINI_API_KEY 设置
    
    voice_settings:
      # 模型选择
      model: "gemini-2.5-flash-preview-tts"  # 或 "gemini-2.5-pro-preview-tts"
      
      # 声音选择（30种可选）
      voice_name: "Kore"  # 默认声音
      # 其他可选声音：Puck, Charon, Fenrir, Aoede, Vale, Journey, 等
      
      # 语言设置
      language: "auto"  # 自动检测语言
```

### 4. 服务注册

在 `src/tts/__init__.py` 中添加：

```python
from .gemini import GeminiTTSService

# 服务注册表
TTS_SERVICES = {
    'gpt_sovits': GPTSoVITSService,
    'gemini': GeminiTTSService,  # 添加Gemini服务
}
```

## 使用方法

### 1. 获取API密钥

1. 访问 [Google AI Studio](https://aistudio.google.com/app/apikey)
2. 创建或选择项目
3. 生成API密钥

### 2. 配置密钥

方式一：环境变量
```bash
export GEMINI_API_KEY="your-api-key-here"
```

方式二：配置文件
```yaml
services:
  gemini:
    enabled: true
    credentials:
      api_key: "your-api-key-here"
```

### 3. 使用命令

```bash
# 使用Gemini TTS（自动输出到SRT文件同目录）
srt2speech input.srt --service gemini

# 指定输出文件
srt2speech input.srt -o custom_output.wav --service gemini

# 使用自定义配置文件（包含声音设置）
srt2speech input.srt --service gemini --config config/gemini_config.yaml
```

## 测试方法

创建 `tests/test_gemini.py`：

```python
"""测试Google Gemini TTS服务"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
from src.config import ConfigManager
from src.tts.gemini import GeminiTTSService

logging.basicConfig(level=logging.INFO)


def test_gemini_tts():
    """测试Gemini TTS基本功能"""
    
    print("=" * 50)
    print("Google Gemini TTS 服务测试")
    print("=" * 50)
    
    # 确保设置了API密钥
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ 请先设置 GEMINI_API_KEY 环境变量")
        return False
    
    try:
        # 1. 初始化服务
        print("\n1. 初始化Gemini服务...")
        config = {
            'credentials': {
                'api_key': os.getenv('GEMINI_API_KEY')
            },
            'voice_settings': {
                'model': 'gemini-2.5-flash-preview-tts',
                'voice_name': 'Kore',
                'language': 'auto'
            }
        }
        
        service = GeminiTTSService(config)
        print("✓ 服务初始化成功")
        
        # 2. 测试中文
        print("\n2. 测试中文转语音...")
        text_zh = "你好，这是Google Gemini的语音合成测试。"
        audio_zh = service.text_to_speech(text_zh)
        print(f"✓ 中文转换成功，音频长度：{len(audio_zh)}ms")
        
        # 3. 测试英文
        print("\n3. 测试英文转语音...")
        text_en = "Hello, this is a test of Google Gemini text-to-speech."
        audio_en = service.text_to_speech(text_en)
        print(f"✓ 英文转换成功，音频长度：{len(audio_en)}ms")
        
        # 4. 测试中英文混合
        print("\n4. 测试中英文混合...")
        text_mixed = "今天我们来测试Gemini TTS的混合语言支持。"
        audio_mixed = service.text_to_speech(text_mixed)
        print(f"✓ 混合语言转换成功，音频长度：{len(audio_mixed)}ms")
        
        # 保存测试音频
        output_dir = Path("tests/output")
        output_dir.mkdir(exist_ok=True)
        
        audio_zh.export(output_dir / "gemini_test_zh.wav", format="wav")
        audio_en.export(output_dir / "gemini_test_en.wav", format="wav")
        audio_mixed.export(output_dir / "gemini_test_mixed.wav", format="wav")
        
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        print(f"音频文件已保存到：{output_dir}")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"❌ 测试失败：{e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return False


def test_voice_options():
    """测试不同声音选项"""
    print("\n\n测试不同声音选项")
    print("=" * 50)
    
    voices = ['Kore', 'Vale', 'Journey', 'Puck', 'Charon']
    print("可用的声音选项：")
    for voice in voices:
        print(f"  - {voice}")
    
    print("\n要测试不同声音，修改配置中的 voice_name 参数")


if __name__ == "__main__":
    if test_gemini_tts():
        test_voice_options()
```

## 注意事项

### 1. API限制
- 预览版本可能有使用限制
- 仅支持纯文本输入（不支持SSML）
- **重要**：API返回的是原始PCM数据，不是WAV格式

### 2. 音频格式
- **API返回格式**：原始PCM数据（非WAV格式）
- **音频参数**：
  - 采样率：24000 Hz
  - 位深：16 bit（2字节）
  - 声道数：1（单声道）
- **处理流程**：
  1. 接收原始PCM数据
  2. 使用wave模块构建WAV文件头
  3. 转换为AudioSegment对象
  4. 转换为项目标准格式（32kHz）

### 3. 错误处理
- API密钥验证
- 网络超时处理
- 服务不可用时的降级

### 4. 最佳实践
- 使用环境变量管理API密钥
- 选择合适的模型（flash为快速，pro为高质量）
- 利用自动语言检测处理混合文本
- 实现重试机制应对临时故障
- **正确处理PCM数据**：不要假设返回的是WAV格式

## 常见问题

### Q: 为什么生成的音频是噪音？
A: 这通常是因为没有正确处理base64编码。Gemini API在某些情况下会返回base64编码的PCM数据，而不是原始二进制数据。我们的实现包含了智能检测机制，会自动识别并解码base64数据。

### Q: 应该使用哪个库？
A: 必须使用 `google-genai` 库，而不是 `google-generativeai`。这是新版API。

### Q: 如何判断数据是否需要base64解码？
A: 我们的实现会自动检测：
- 如果数据是字符串类型，尝试base64解码
- 如果是bytes类型，尝试验证是否为base64编码
- 通过数据长度和格式特征判断是否解码成功

## 与GPT-SoVITS的对比

| 特性 | Gemini TTS | GPT-SoVITS |
|------|------------|------------|
| 部署方式 | 云端API | 本地部署 |
| 语言支持 | 24种语言 | 5种语言 |
| 声音选择 | 30种预设 | 自定义声音克隆 |
| 音质 | 高质量 | 极高质量 |
| 延迟 | 取决于网络 | 低延迟 |
| 成本 | 按使用量计费 | 免费（需GPU） |
| 适用场景 | 多语言、快速部署 | 声音克隆、离线使用 |

## 未来扩展

1. **高级功能**
   - 支持更多声音参数调整
   - 实现批量处理优化
   - 添加缓存机制

2. **集成优化**
   - 与服务降级机制深度集成
   - 添加使用统计和监控
   - 支持流式处理

3. **用户体验**
   - 声音预览功能
   - 自动选择最佳声音
   - 语言检测优化