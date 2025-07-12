# GPT-SoVITS 快速开始指南

本指南帮助您快速开始使用GPT-SoVITS进行字幕转语音。

## 前置准备

### 1. 安装GPT-SoVITS

请参考[GPT-SoVITS官方仓库](https://github.com/RVC-Boss/GPT-SoVITS)进行安装。

### 2. 下载预训练模型

确保已下载必需的预训练模型：
- 中文BERT模型：`chinese-roberta-wwm-ext-large`
- 中文Hubert模型：`chinese-hubert-base`
- GPT模型：如 `s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt`
- SoVITS模型：如 `s2G488k.pth`

## 快速开始

### 步骤1：启动GPT-SoVITS服务

```bash
cd /path/to/GPT-SoVITS
python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

### 步骤2：准备参考音频

1. 录制一段3-10秒的清晰语音
2. 保存为WAV格式（建议16kHz或以上采样率）
3. 准备对应的文本内容

示例参考音频要求：
- 时长：3-10秒
- 格式：WAV
- 内容：清晰的普通话发音
- 环境：安静，无背景噪音

### 步骤3：创建配置文件

创建 `config/my_gptsovits.yaml`：

```yaml
services:
  gpt_sovits:
    service_name: gpt_sovits
    priority: 1
    enabled: true
    credentials:
      api_url: "http://127.0.0.1:9880"
      api_version: "v2"
    voice_settings:
      language: "zh"
      ref_audio_path: "/path/to/your/reference.wav"  # 修改为您的参考音频路径
      prompt_text: "这里填写参考音频的文本内容"       # 修改为对应文本
      prompt_lang: "zh"
      temperature: 0.3  # 降低以获得更稳定的输出
      top_k: 5
      top_p: 0.7
      speed_factor: 1.0
```

### 步骤4：运行转换

```bash
# 转换整个SRT文件
python -m src.cli input.srt output.wav -c config/my_gptsovits.yaml

# 预览模式（只处理前3条字幕）
python -m src.cli input.srt output.wav -c config/my_gptsovits.yaml --preview 3

# 启用调试模式查看详细信息
python -m src.cli input.srt output.wav -c config/my_gptsovits.yaml --debug
```

## 参数调优

### 语音质量参数

- **temperature** (0.1-2.0)：控制随机性，越低越稳定
  - 推荐值：0.3-0.7
  - 新闻播报：0.3
  - 自然对话：0.7

- **top_k** (1-20)：限制采样候选数量
  - 推荐值：5-10
  - 更稳定：3-5
  - 更多样：10-15

- **top_p** (0-1)：核采样阈值
  - 推荐值：0.7-0.9
  - 配合top_k使用

### 语速控制

- **speed_factor** (0.5-2.0)：语速倍率
  - 1.0：正常语速
  - 0.8：慢速
  - 1.2：快速

### 文本分割

- **text_split_method**：
  - `cut0`：不分割（短文本）
  - `cut5`：按标点分割（推荐）
  - `cut2`：按50字分割

## 常见问题

### 1. 声音不像参考音频

- 确保参考音频质量良好
- 参考音频文本必须准确匹配
- 尝试使用更长的参考音频（5-10秒）
- 调整temperature参数

### 2. 生成速度慢

- 使用GPU加速
- 减小batch_size
- 启用流式模式
- 使用更短的文本分割

### 3. 内存不足

- 在GPT-SoVITS配置中启用半精度：`is_half: true`
- 减小batch_size为1
- 分批处理长文本

## 高级用法

### 使用多个参考音频

```yaml
voice_settings:
  aux_ref_audio_paths:
    - "ref1.wav"
    - "ref2.wav"
  # 可实现多角色音色融合
```

### 流式处理

```yaml
voice_settings:
  streaming_mode: true
  # 适合处理超长文本
```

### 情感控制

通过调整参数组合实现不同情感：

**严肃/新闻播报**：
```yaml
temperature: 0.3
top_k: 3
speed_factor: 0.9
```

**活泼/对话**：
```yaml
temperature: 0.8
top_k: 10
speed_factor: 1.1
```

## 性能优化建议

1. **GPU加速**：确保GPT-SoVITS使用CUDA
2. **批处理**：合理设置batch_size（GPU显存允许范围内）
3. **缓存**：启用srt2speech的缓存功能避免重复生成
4. **并行处理**：保持`parallel_infer: true`

## 下一步

- 查看[完整配置选项](../config/default.yaml)
- 阅读[GPT-SoVITS技术文档](tts-api-reference/GPT-SoVITS技术文档.md)
- 尝试不同的参考音频和参数组合