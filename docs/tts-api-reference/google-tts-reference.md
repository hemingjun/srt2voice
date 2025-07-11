# Google Cloud Text-to-Speech API 参考文档

## 概述
Google Cloud Text-to-Speech API 允许开发者将文本转换为自然流畅的语音。支持多种语言和声音，包括 WaveNet 和 Neural2 等高质量语音模型。

## 安装

### Python SDK 安装
```bash
pip install google-cloud-texttospeech
```

### 环境要求
- Python 3.7+
- Google Cloud 项目和认证凭据

## 基础使用

### 1. 导入和初始化
```python
from google.cloud import texttospeech

# 创建客户端实例
client = texttospeech.TextToSpeechClient()
```

### 2. 基本语音合成
```python
# 设置要合成的文本
synthesis_input = texttospeech.SynthesisInput(text="你好，世界！")

# 设置声音参数
voice = texttospeech.VoiceSelectionParams(
    language_code="zh-CN",  # 中文（中国大陆）
    name="zh-CN-Wavenet-A",  # 具体的声音模型
    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
)

# 设置音频配置
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)

# 执行语音合成请求
response = client.synthesize_speech(
    input=synthesis_input,
    voice=voice,
    audio_config=audio_config
)

# 保存音频文件
with open("output.mp3", "wb") as out:
    out.write(response.audio_content)
```

## 声音选项

### 推荐的中文声音
| 声音ID | 性别 | 类型 | 描述 |
|--------|------|------|------|
| zh-CN-Wavenet-A | 女声 | WaveNet | 自然流畅的女声 |
| zh-CN-Wavenet-B | 男声 | WaveNet | 成熟稳重的男声 |
| zh-CN-Wavenet-C | 男声 | WaveNet | 年轻活力的男声 |
| zh-CN-Wavenet-D | 女声 | WaveNet | 温柔甜美的女声 |
| zh-CN-Neural2-A | 女声 | Neural2 | 最新一代神经网络女声 |
| zh-CN-Neural2-B | 女声 | Neural2 | 专业播音女声 |
| zh-CN-Neural2-C | 男声 | Neural2 | 专业播音男声 |
| zh-CN-Neural2-D | 男声 | Neural2 | 富有磁性的男声 |

### 获取可用声音列表
```python
# 列出所有可用的声音
voices = client.list_voices()

# 筛选中文声音
for voice in voices.voices:
    if voice.language_codes[0].startswith("zh-CN"):
        print(f"Name: {voice.name}")
        print(f"Language: {voice.language_codes[0]}")
        print(f"Gender: {voice.ssml_gender}")
        print(f"Natural sample rate: {voice.natural_sample_rate_hertz} Hz")
        print("---")
```

## SSML 支持

### 使用 SSML 进行高级控制
```python
# SSML 输入示例
ssml_text = """
<speak>
    <prosody rate="90%" pitch="-2st">
        这是一段语速较慢、音调较低的文本。
    </prosody>
    <break time="500ms"/>
    <emphasis level="strong">这部分需要强调。</emphasis>
    <prosody rate="110%">
        这段话的语速会快一些。
    </prosody>
</speak>
"""

synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
```

### SSML 标签说明
- `<prosody>`: 控制语速、音调、音量
  - `rate`: 语速（如 "90%", "slow", "fast"）
  - `pitch`: 音调（如 "+5st", "-2st", "high", "low"）
  - `volume`: 音量（如 "+6dB", "loud", "soft"）
- `<break>`: 插入停顿（如 "500ms", "1s"）
- `<emphasis>`: 强调级别（"strong", "moderate", "reduced"）
- `<say-as>`: 指定文本类型（如日期、时间、数字）

## 音频配置选项

### 支持的音频格式
```python
# WAV 格式（无损）
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000  # 可选：8000, 16000, 24000, 48000
)

# MP3 格式（有损压缩）
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)

# OGG Opus 格式（适合流媒体）
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.OGG_OPUS
)
```

### 音频效果配置
```python
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    speaking_rate=1.0,  # 语速倍率 (0.25 - 4.0)
    pitch=0.0,  # 音调偏移 (-20.0 - 20.0 半音)
    volume_gain_db=0.0,  # 音量增益 (-96.0 - 16.0 dB)
    effects_profile_id=["headphone-class-device"]  # 音频优化配置
)
```

## 情感控制映射

### Google TTS 情感参数建议
```python
# 情感到参数的映射
emotion_mappings = {
    "emphasis": {
        "speaking_rate": 0.9,
        "pitch": 2.0,  # 半音
        "volume_gain_db": 2.0
    },
    "friendly": {
        "speaking_rate": 1.0,
        "pitch": 1.0,
        "volume_gain_db": 0.0
    },
    "neutral": {
        "speaking_rate": 1.0,
        "pitch": 0.0,
        "volume_gain_db": 0.0
    },
    "professional": {
        "speaking_rate": 0.95,
        "pitch": -0.5,
        "volume_gain_db": 0.0
    }
}
```

## 长文本处理

### 处理长文本的最佳实践
```python
def synthesize_long_text(text, max_chars=5000):
    """分段处理长文本"""
    # Google TTS 单次请求最大支持 5000 字符
    segments = []
    
    # 按句子分割，避免在句子中间断开
    sentences = text.split('。')
    current_segment = ""
    
    for sentence in sentences:
        if len(current_segment) + len(sentence) + 1 <= max_chars:
            current_segment += sentence + '。'
        else:
            if current_segment:
                segments.append(current_segment)
            current_segment = sentence + '。'
    
    if current_segment:
        segments.append(current_segment)
    
    # 合成每个片段
    audio_segments = []
    for segment in segments:
        synthesis_input = texttospeech.SynthesisInput(text=segment)
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        audio_segments.append(response.audio_content)
    
    return audio_segments
```

## 错误处理

### 常见错误和解决方案
```python
from google.api_core import exceptions

try:
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
except exceptions.InvalidArgument as e:
    print(f"请求参数错误: {e}")
except exceptions.PermissionDenied as e:
    print(f"权限不足: {e}")
except exceptions.ResourceExhausted as e:
    print(f"配额已用尽: {e}")
except exceptions.DeadlineExceeded as e:
    print(f"请求超时: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 性能优化

### 1. 批量处理
```python
# 对于多个文本，可以并发处理
import concurrent.futures

def synthesize_batch(texts):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for text in texts:
            future = executor.submit(synthesize_single_text, text)
            futures.append(future)
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    return results
```

### 2. 缓存机制
```python
import hashlib
import os

def get_cached_or_synthesize(text, voice_params, audio_config):
    # 生成缓存键
    cache_key = hashlib.md5(
        f"{text}{voice_params}{audio_config}".encode()
    ).hexdigest()
    
    cache_path = f"cache/{cache_key}.mp3"
    
    # 检查缓存
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return f.read()
    
    # 合成新音频
    response = synthesize_text(text, voice_params, audio_config)
    
    # 保存到缓存
    os.makedirs("cache", exist_ok=True)
    with open(cache_path, "wb") as f:
        f.write(response.audio_content)
    
    return response.audio_content
```

## 认证配置

### 使用服务账号密钥
```python
from google.oauth2 import service_account

# 方法1：使用环境变量
# export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"

# 方法2：代码中指定
credentials = service_account.Credentials.from_service_account_file(
    "path/to/key.json"
)
client = texttospeech.TextToSpeechClient(credentials=credentials)

# 方法3：使用 API 密钥（仅限某些场景）
# 需要在请求中添加 key 参数
```

## 配额和限制

### API 配额
- 每分钟字符数：100万字符
- 每分钟请求数：1000个请求
- 单个请求最大字符数：5000字符（SSML）

### 价格说明
- 标准声音：每100万字符 $4.00
- WaveNet 声音：每100万字符 $16.00
- Neural2 声音：每100万字符 $16.00

## 最佳实践

1. **选择合适的声音**：Neural2 和 WaveNet 声音质量更高，但成本也更高
2. **使用 SSML**：获得更精细的语音控制
3. **实现重试机制**：处理临时性错误
4. **缓存结果**：避免重复合成相同的文本
5. **监控配额使用**：避免超出限制
6. **批量处理**：提高效率，但注意并发限制

## 相关资源
- [官方文档](https://cloud.google.com/text-to-speech/docs)
- [API 参考](https://cloud.google.com/python/docs/reference/texttospeech/latest)
- [价格计算器](https://cloud.google.com/products/calculator)
- [配额和限制](https://cloud.google.com/text-to-speech/quotas)