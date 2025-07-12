# GPT-SoVITS 技术使用文档

## 概述

GPT-SoVITS 是一个基于深度学习的语音合成系统，支持零样本语音克隆功能。本文档详细介绍如何在 srt2speech 项目中集成 GPT-SoVITS 本地服务。

## 系统架构

### 核心组件
- **GPT模型**：负责文本到语义的转换
- **SoVITS模型**：负责语义到语音的合成
- **API服务**：提供 HTTP 接口供外部调用

### 支持版本
- v1：基础版本
- v2：增强版本（推荐）
- v3：支持更多采样参数
- v4：最新版本

## API 接口说明

### 1. API v1（基础版）

#### 启动服务
```bash
python api.py -dr "reference.wav" -dt "参考音频文本" -dl "zh" -p 9880
```

#### 主要参数
- `-s`：SoVITS模型路径
- `-g`：GPT模型路径
- `-dr`：默认参考音频路径
- `-dt`：默认参考音频文本
- `-dl`：默认参考音频语言（zh/en/ja/ko/yue）
- `-d`：推理设备（cuda/cpu）
- `-p`：服务端口（默认9880）
- `-fp`：使用全精度
- `-hp`：使用半精度
- `-sm`：流式返回模式
- `-mt`：音频格式（wav/ogg/aac）

#### 基础推理接口

**使用默认参考音频**
```python
import requests

# GET请求
url = "http://127.0.0.1:9880"
params = {
    "text": "要合成的文本内容",
    "text_language": "zh"
}
response = requests.get(url, params=params)

# 保存音频
with open("output.wav", "wb") as f:
    f.write(response.content)
```

**指定参考音频**
```python
params = {
    "text": "要合成的文本内容",
    "text_language": "zh",
    "refer_wav_path": "path/to/reference.wav",
    "prompt_text": "参考音频的文本内容",
    "prompt_language": "zh"
}
response = requests.get(url, params=params)
```

**高级参数**
```python
params = {
    "text": "要合成的文本内容",
    "text_language": "zh",
    "refer_wav_path": "reference.wav",
    "prompt_text": "参考音频文本",
    "prompt_language": "zh",
    "top_k": 20,          # Top-K采样
    "top_p": 0.6,         # Top-P采样
    "temperature": 0.6,   # 温度参数
    "speed": 1.0,         # 语速
    "cut_punc": "，。",    # 文本切分符号
    "inp_refs": ["ref1.wav", "ref2.wav"]  # 多参考音频
}
```

### 2. API v2（推荐版本）

#### 启动服务
```bash
python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

#### TTS推理接口 `/tts`

**完整参数说明**
```python
import requests
import json

url = "http://127.0.0.1:9880/tts"
data = {
    "text": "要合成的文本",                      # 必需
    "text_lang": "zh",                         # 必需：语言（zh/en/ja/ko/yue）
    "ref_audio_path": "reference.wav",         # 必需：参考音频路径
    "aux_ref_audio_paths": [],                 # 可选：辅助参考音频（多角色融合）
    "prompt_text": "参考音频的文本",             # 必需：参考音频文本
    "prompt_lang": "zh",                       # 必需：参考音频语言
    "top_k": 5,                               # Top-K采样（默认5）
    "top_p": 1,                               # Top-P采样（默认1）
    "temperature": 1,                         # 温度参数（默认1）
    "text_split_method": "cut5",              # 文本分割方法
    "batch_size": 1,                          # 批处理大小
    "batch_threshold": 0.75,                  # 批处理阈值
    "split_bucket": True,                     # 是否分桶处理
    "speed_factor": 1.0,                      # 语速因子
    "fragment_interval": 0.3,                 # 片段间隔
    "seed": -1,                               # 随机种子（-1为随机）
    "media_type": "wav",                      # 输出格式
    "streaming_mode": False,                  # 是否流式返回
    "parallel_infer": True,                   # 是否并行推理
    "repetition_penalty": 1.35,               # 重复惩罚
    "sample_steps": 32,                       # V3版本采样步数
    "super_sampling": False                   # V3版本超采样
}

response = requests.post(url, json=data)

# 处理响应
if response.status_code == 200:
    # 非流式模式：直接保存
    with open("output.wav", "wb") as f:
        f.write(response.content)
else:
    print(f"错误：{response.json()}")
```

**流式响应处理**
```python
data["streaming_mode"] = True
response = requests.post(url, json=data, stream=True)

if response.status_code == 200:
    with open("output.wav", "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
```

#### 模型切换接口

**切换GPT模型**
```python
url = "http://127.0.0.1:9880/set_gpt_weights"
params = {"weights_path": "path/to/gpt/model.ckpt"}
response = requests.get(url, params=params)
```

**切换SoVITS模型**
```python
url = "http://127.0.0.1:9880/set_sovits_weights"
params = {"weights_path": "path/to/sovits/model.pth"}
response = requests.get(url, params=params)
```

## 文本分割方法

GPT-SoVITS 提供多种文本分割方法，通过 `text_split_method` 参数指定：

- `cut0`：不切分
- `cut1`：按句号切分
- `cut2`：按50字切分
- `cut3`：按中文句号切分
- `cut4`：按英文句号切分
- `cut5`：按标点符号切分（推荐）

## 配置文件说明

### tts_infer.yaml 结构
```yaml
v2:  # 版本配置
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
  device: cuda  # 或 cpu
  is_half: true  # 是否使用半精度
  t2s_weights_path: path/to/gpt/model.ckpt
  version: v2
  vits_weights_path: path/to/sovits/model.pth
```

## 在 srt2speech 中的集成方案

### 1. 服务配置结构
```yaml
services:
  gpt_sovits:
    service_name: gpt_sovits
    priority: 1
    enabled: true
    credentials:
      api_url: "http://127.0.0.1:9880"
      api_version: "v2"  # 或 "v1"
    voice_settings:
      # 基础设置
      language: "zh"
      ref_audio_path: "reference.wav"  # 相对于GPT-SoVITS根目录
      prompt_text: "这是参考音频的文本内容"
      prompt_lang: "zh"
      
      # 高级参数
      top_k: 5
      top_p: 1
      temperature: 1
      speed_factor: 1.0
      text_split_method: "cut5"
      batch_size: 1
      media_type: "wav"
      streaming_mode: false
      
      # V3版本参数
      sample_steps: 32
      super_sampling: false
```

### 2. Python 集成示例

```python
import requests
from pathlib import Path
from pydub import AudioSegment
import io

class GPTSoVITSService:
    def __init__(self, config):
        self.api_url = config['credentials']['api_url']
        self.api_version = config['credentials'].get('api_version', 'v2')
        self.voice_settings = config['voice_settings']
        self.validate_service()
    
    def validate_service(self):
        """验证服务是否可用"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=5)
            return response.status_code < 500
        except:
            return False
    
    def text_to_speech(self, text: str) -> AudioSegment:
        """将文本转换为语音"""
        if self.api_version == 'v2':
            url = f"{self.api_url}/tts"
            data = {
                "text": text,
                "text_lang": self.voice_settings['language'],
                "ref_audio_path": self.voice_settings['ref_audio_path'],
                "prompt_text": self.voice_settings['prompt_text'],
                "prompt_lang": self.voice_settings['prompt_lang'],
                **{k: v for k, v in self.voice_settings.items() 
                   if k not in ['language', 'ref_audio_path', 'prompt_text', 'prompt_lang']}
            }
            response = requests.post(url, json=data)
        else:  # v1
            url = self.api_url
            params = {
                "text": text,
                "text_language": self.voice_settings['language'],
                "refer_wav_path": self.voice_settings['ref_audio_path'],
                "prompt_text": self.voice_settings['prompt_text'],
                "prompt_language": self.voice_settings['prompt_lang']
            }
            response = requests.get(url, params=params)
        
        if response.status_code == 200:
            # 将响应转换为AudioSegment
            audio_data = io.BytesIO(response.content)
            return AudioSegment.from_wav(audio_data)
        else:
            raise Exception(f"TTS请求失败：{response.status_code}")
```

## 性能优化建议

1. **使用GPU加速**：在配置中设置 `device: cuda`
2. **启用半精度**：设置 `is_half: true` 可减少显存占用
3. **批处理**：合理设置 `batch_size` 提高效率
4. **流式模式**：对于长文本使用 `streaming_mode: true`
5. **并行推理**：保持 `parallel_infer: true`

## 常见问题

### 1. 服务启动失败
- 检查模型文件路径是否正确
- 确认依赖已正确安装
- 检查端口是否被占用

### 2. 生成质量问题
- 调整 `temperature` 参数（降低获得更稳定输出）
- 调整 `top_k` 和 `top_p` 参数
- 使用高质量的参考音频

### 3. 性能问题
- 使用GPU而非CPU
- 启用半精度计算
- 减小 `batch_size`
- 使用更快的文本分割方法

## 错误处理

```python
def safe_tts_request(text, max_retries=3):
    """带重试机制的TTS请求"""
    for i in range(max_retries):
        try:
            audio = tts_service.text_to_speech(text)
            return audio
        except requests.exceptions.ConnectionError:
            if i == max_retries - 1:
                raise Exception("GPT-SoVITS服务连接失败")
            time.sleep(1)
        except Exception as e:
            if "CUDA out of memory" in str(e):
                # 降低batch_size后重试
                tts_service.voice_settings['batch_size'] = 1
            else:
                raise
```

## 总结

GPT-SoVITS 提供了强大的本地语音合成能力，通过合理配置和使用，可以在 srt2speech 项目中实现高质量的字幕转语音功能。建议优先使用 API v2 版本，它提供了更丰富的参数控制和更好的性能。