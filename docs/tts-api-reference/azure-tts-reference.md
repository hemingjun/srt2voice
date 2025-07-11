# Azure Cognitive Services Speech SDK 参考文档

## 概述
Azure Cognitive Services Speech SDK 提供了强大的文本转语音（TTS）功能，支持多种语言和神经网络声音，具有丰富的 SSML 支持和情感控制能力。

## 安装

### Python SDK 安装
```bash
pip install azure-cognitiveservices-speech
```

### 环境要求
- Python 3.7+
- Azure 订阅和 Speech Service 资源

## 基础使用

### 1. 导入和初始化
```python
import azure.cognitiveservices.speech as speechsdk

# 创建语音配置
speech_key = "YourSubscriptionKey"
service_region = "eastasia"  # 例如：eastasia, westus, westeurope

speech_config = speechsdk.SpeechConfig(
    subscription=speech_key, 
    region=service_region
)
```

### 2. 基本语音合成
```python
# 设置语音
speech_config.speech_synthesis_voice_name = "zh-CN-XiaoxiaoNeural"

# 创建语音合成器
speech_synthesizer = speechsdk.SpeechSynthesizer(
    speech_config=speech_config
)

# 合成语音
text = "你好，欢迎使用Azure语音服务！"
result = speech_synthesizer.speak_text_async(text).get()

# 检查结果
if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("语音合成成功")
elif result.reason == speechsdk.ResultReason.Canceled:
    cancellation_details = result.cancellation_details
    print(f"语音合成取消: {cancellation_details.reason}")
    if cancellation_details.reason == speechsdk.CancellationReason.Error:
        print(f"错误详情: {cancellation_details.error_details}")
```

### 3. 保存到文件
```python
# 配置音频输出到文件
audio_config = speechsdk.audio.AudioOutputConfig(
    filename="output.wav"
)

# 创建带音频配置的合成器
speech_synthesizer = speechsdk.SpeechSynthesizer(
    speech_config=speech_config,
    audio_config=audio_config
)

# 合成并保存
result = speech_synthesizer.speak_text_async(text).get()
```

## 声音选项

### 推荐的中文神经网络声音
| 声音名称 | 性别 | 风格 | 描述 |
|----------|------|------|------|
| zh-CN-XiaoxiaoNeural | 女声 | 多种 | 最受欢迎，支持多种说话风格 |
| zh-CN-YunxiNeural | 男声 | 多种 | 成熟男声，支持多种风格 |
| zh-CN-YunjianNeural | 男声 | 多种 | 新闻播报风格 |
| zh-CN-XiaoyiNeural | 女声 | 标准 | 年轻活泼的女声 |
| zh-CN-YunyangNeural | 男声 | 专业 | 专业播音男声 |
| zh-CN-XiaochenNeural | 女声 | 优雅 | 温柔优雅的女声 |
| zh-CN-XiaohanNeural | 女声 | 平静 | 平静舒缓的女声 |
| zh-CN-XiaomengNeural | 女声 | 可爱 | 甜美可爱的女声 |
| zh-CN-XiaomoNeural | 女声 | 成熟 | 成熟知性的女声 |
| zh-CN-XiaoqiuNeural | 女声 | 活泼 | 活泼开朗的女声 |
| zh-CN-XiaoruiNeural | 女声 | 老年 | 老年女声 |
| zh-CN-XiaoshuangNeural | 女声 | 童声 | 儿童女声 |
| zh-CN-XiaoxuanNeural | 女声 | 专业 | 专业客服女声 |
| zh-CN-XiaoyanNeural | 女声 | 专业 | 专业播音女声 |
| zh-CN-XiaoyouNeural | 女声 | 童声 | 儿童女声 |
| zh-CN-XiaozhenNeural | 女声 | 专业 | 专业严肃的女声 |
| zh-CN-YunfengNeural | 男声 | 专业 | 专业男声 |
| zh-CN-YunhaoNeural | 男声 | 专业 | 广告配音男声 |
| zh-CN-YunxiaNeural | 男声 | 童声 | 儿童男声 |
| zh-CN-YunyeNeural | 男声 | 专业 | 成熟稳重男声 |
| zh-CN-YunzeNeural | 男声 | 老年 | 老年男声 |

### 获取可用声音列表
```python
# 创建语音合成器
synthesizer = speechsdk.SpeechSynthesizer(
    speech_config=speech_config, 
    audio_config=None
)

# 获取声音列表
result = synthesizer.get_voices_async().get()

if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
    # 筛选中文声音
    for voice in result.voices:
        if voice.locale.startswith("zh-CN"):
            print(f"Voice: {voice.short_name}")
            print(f"Locale: {voice.locale}")
            print(f"Gender: {voice.gender}")
            print(f"Style list: {voice.style_list}")
            print("---")
```

## SSML 支持

### 使用 SSML 进行高级控制
```python
ssml_text = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
       xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN">
    <voice name="zh-CN-XiaoxiaoNeural">
        <mstts:express-as style="cheerful">
            你好！很高兴见到你！
        </mstts:express-as>
        <break time="500ms"/>
        <prosody rate="-10%" pitch="-5%">
            让我用慢一点的语速说话。
        </prosody>
        <mstts:express-as style="newscast">
            下面播报一条新闻。
        </mstts:express-as>
    </voice>
</speak>
"""

result = speech_synthesizer.speak_ssml_async(ssml_text).get()
```

### Azure 特有的 SSML 扩展

#### 1. 说话风格（仅限支持的声音）
```xml
<!-- XiaoxiaoNeural 支持的风格 -->
<mstts:express-as style="newscast">新闻播报风格</mstts:express-as>
<mstts:express-as style="customerservice">客服风格</mstts:express-as>
<mstts:express-as style="assistant">助手风格</mstts:express-as>
<mstts:express-as style="chat">聊天风格</mstts:express-as>
<mstts:express-as style="cheerful">愉快风格</mstts:express-as>
<mstts:express-as style="empathetic">同情风格</mstts:express-as>
<mstts:express-as style="newscast-casual">轻松新闻风格</mstts:express-as>
<mstts:express-as style="embarrassed">尴尬风格</mstts:express-as>
<mstts:express-as style="fearful">恐惧风格</mstts:express-as>
<mstts:express-as style="gentle">温柔风格</mstts:express-as>
<mstts:express-as style="depressed">沮丧风格</mstts:express-as>
<mstts:express-as style="serious">严肃风格</mstts:express-as>
<mstts:express-as style="angry">生气风格</mstts:express-as>
<mstts:express-as style="sad">悲伤风格</mstts:express-as>
```

#### 2. 角色扮演（仅限 YunxiNeural）
```xml
<mstts:express-as role="Boy">男孩声音</mstts:express-as>
<mstts:express-as role="Girl">女孩声音</mstts:express-as>
<mstts:express-as role="OlderAdultMale">老年男性</mstts:express-as>
<mstts:express-as role="OlderAdultFemale">老年女性</mstts:express-as>
```

#### 3. 风格强度控制
```xml
<mstts:express-as style="cheerful" styledegree="2">
    非常愉快的语气！
</mstts:express-as>
```

## 音频配置选项

### 输出格式配置
```python
# 设置音频输出格式
speech_config.set_speech_synthesis_output_format(
    speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
)

# 常用格式选项：
# - Riff16Khz16BitMonoPcm (WAV, 16kHz, 16-bit, 单声道)
# - Riff24Khz16BitMonoPcm (WAV, 24kHz, 16-bit, 单声道)
# - Riff48Khz16BitMonoPcm (WAV, 48kHz, 16-bit, 单声道)
# - Audio16Khz32KBitRateMonoMp3 (MP3, 16kHz, 32kbps)
# - Audio24Khz48KBitRateMonoMp3 (MP3, 24kHz, 48kbps)
# - Audio24Khz96KBitRateMonoMp3 (MP3, 24kHz, 96kbps)
```

### 流式音频输出
```python
# 配置流式输出
def synthesize_to_stream():
    # 使用拉流
    stream = speechsdk.AudioDataStream(result)
    
    # 保存到文件
    stream.save_to_wav_file("output.wav")
    
    # 或逐块读取
    audio_buffer = bytes(32000)
    filled_size = stream.read_data(audio_buffer)
    while filled_size > 0:
        # 处理音频数据
        process_audio_chunk(audio_buffer[:filled_size])
        filled_size = stream.read_data(audio_buffer)
```

## 情感控制映射

### Azure TTS 情感参数建议
```python
# 使用 SSML express-as 标签
emotion_mappings = {
    "emphasis": {
        "style": "newscast",
        "styledegree": "1.5",
        "prosody": {"rate": "-10%", "pitch": "+10%"}
    },
    "friendly": {
        "style": "cheerful",
        "styledegree": "1.0",
        "prosody": {"rate": "+0%", "pitch": "+5%"}
    },
    "neutral": {
        "style": "chat",
        "styledegree": "1.0",
        "prosody": {"rate": "+0%", "pitch": "+0%"}
    },
    "professional": {
        "style": "newscast",
        "styledegree": "1.0",
        "prosody": {"rate": "-5%", "pitch": "-2%"}
    }
}

def generate_ssml_with_emotion(text, emotion="neutral"):
    mapping = emotion_mappings.get(emotion, emotion_mappings["neutral"])
    
    ssml = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
           xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN">
        <voice name="zh-CN-XiaoxiaoNeural">
            <mstts:express-as style="{mapping['style']}" 
                              styledegree="{mapping['styledegree']}">
                <prosody rate="{mapping['prosody']['rate']}" 
                         pitch="{mapping['prosody']['pitch']}">
                    {text}
                </prosody>
            </mstts:express-as>
        </voice>
    </speak>
    """
    return ssml
```

## 批量和异步处理

### 批量文本合成
```python
import asyncio

async def synthesize_batch_async(texts):
    tasks = []
    for i, text in enumerate(texts):
        # 为每个文本创建单独的音频配置
        audio_config = speechsdk.audio.AudioOutputConfig(
            filename=f"output_{i}.wav"
        )
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # 添加异步任务
        task = synthesizer.speak_text_async(text)
        tasks.append(task)
    
    # 等待所有任务完成
    results = []
    for task in tasks:
        result = task.get()
        results.append(result)
    
    return results
```

### 使用回调处理事件
```python
def setup_callbacks(synthesizer):
    # 合成开始
    synthesizer.synthesis_started.connect(
        lambda evt: print(f"合成开始: {evt}")
    )
    
    # 合成中（接收音频数据）
    synthesizer.synthesizing.connect(
        lambda evt: print(f"接收音频数据: {len(evt.result.audio_data)} 字节")
    )
    
    # 合成完成
    synthesizer.synthesis_completed.connect(
        lambda evt: print(f"合成完成: {evt}")
    )
    
    # 合成取消
    synthesizer.synthesis_canceled.connect(
        lambda evt: print(f"合成取消: {evt.result.cancellation_details.reason}")
    )
```

## 错误处理

### 完整的错误处理示例
```python
def synthesize_with_error_handling(text):
    try:
        result = speech_synthesizer.speak_text_async(text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("成功合成语音")
            return result.audio_data
            
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"语音合成被取消: {cancellation_details.reason}")
            
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"错误代码: {cancellation_details.error_code}")
                print(f"错误详情: {cancellation_details.error_details}")
                
                # 常见错误处理
                if "401" in str(cancellation_details.error_details):
                    raise Exception("认证失败：请检查订阅密钥")
                elif "403" in str(cancellation_details.error_details):
                    raise Exception("访问被拒绝：请检查服务区域")
                elif "429" in str(cancellation_details.error_details):
                    raise Exception("请求过多：已达到速率限制")
                elif "ConnectionFailure" in str(cancellation_details.reason):
                    raise Exception("连接失败：请检查网络连接")
                    
            return None
            
    except Exception as e:
        print(f"发生异常: {e}")
        raise
```

## 性能优化

### 1. 连接池和复用
```python
# 复用语音合成器实例
class SpeechSynthesizerPool:
    def __init__(self, speech_config, pool_size=5):
        self.synthesizers = []
        for _ in range(pool_size):
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=None  # 使用内存输出
            )
            self.synthesizers.append(synthesizer)
        self.current = 0
    
    def get_synthesizer(self):
        synthesizer = self.synthesizers[self.current]
        self.current = (self.current + 1) % len(self.synthesizers)
        return synthesizer
```

### 2. 预连接和预热
```python
def warm_up_connection(synthesizer):
    """预热连接，减少首次请求延迟"""
    # 合成一个很短的文本来建立连接
    synthesizer.speak_text_async("测试").get()
```

### 3. 缓存实现
```python
import hashlib
import pickle
import os

class TTSCache:
    def __init__(self, cache_dir="tts_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_key(self, text, voice_name, style=None):
        key_string = f"{text}_{voice_name}_{style}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, text, voice_name, style=None):
        cache_key = self.get_cache_key(text, voice_name, style)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.wav")
        
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                return f.read()
        return None
    
    def set(self, text, voice_name, audio_data, style=None):
        cache_key = self.get_cache_key(text, voice_name, style)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.wav")
        
        with open(cache_path, "wb") as f:
            f.write(audio_data)
```

## 高级功能

### 1. 字级时间戳
```python
# 启用字级时间戳
speech_config.request_word_level_timestamps()

# 处理时间戳信息
def on_word_boundary(evt):
    print(f"Word: {evt.text}")
    print(f"Offset: {evt.audio_offset / 10000}ms")
    print(f"Duration: {evt.duration / 10000}ms")

synthesizer.synthesis_word_boundary.connect(on_word_boundary)
```

### 2. 视觉素材（口型同步）
```python
# 启用视觉素材
speech_config.request_viseme_data()

# 处理视觉素材事件
def on_viseme(evt):
    print(f"Viseme ID: {evt.viseme_id}")
    print(f"Audio offset: {evt.audio_offset / 10000}ms")

synthesizer.viseme_received.connect(on_viseme)
```

### 3. 自定义语音模型
```python
# 使用自定义语音模型（需要先训练）
speech_config.endpoint_id = "YourCustomVoiceEndpointId"
speech_config.speech_synthesis_voice_name = "YourCustomVoiceName"
```

## 配额和限制

### API 限制
- 并发请求：根据订阅层级而定（F0: 20, S0: 100+）
- 最大文本长度：单个请求最多 10 分钟的音频
- 请求频率：F0 层每秒 20 个请求，S0 层更高

### 价格说明（S0 标准层）
- 神经网络声音：每 100 万字符 $16
- 标准声音：每 100 万字符 $4
- 自定义神经网络声音：每 100 万字符 $24
- 长音频创建：每 100 万字符 $100

## 最佳实践

1. **选择合适的区域**：选择离用户最近的 Azure 区域以减少延迟
2. **使用神经网络声音**：获得更自然的语音效果
3. **利用 SSML**：充分利用 Azure 的扩展 SSML 功能
4. **实现重试机制**：处理临时性错误和速率限制
5. **批量处理优化**：合理使用异步和并发
6. **监控使用情况**：跟踪 API 调用和字符使用量
7. **缓存策略**：对常用文本实施缓存

## 相关资源
- [官方文档](https://docs.microsoft.com/azure/cognitive-services/speech-service/)
- [Python SDK 参考](https://docs.microsoft.com/python/api/azure-cognitiveservices-speech/)
- [SSML 参考](https://docs.microsoft.com/azure/cognitive-services/speech-service/speech-synthesis-markup)
- [支持的语言和声音](https://docs.microsoft.com/azure/cognitive-services/speech-service/language-support#text-to-speech)
- [价格详情](https://azure.microsoft.com/pricing/details/cognitive-services/speech-services/)
- [配额和限制](https://docs.microsoft.com/azure/cognitive-services/speech-service/speech-services-quotas-and-limits)