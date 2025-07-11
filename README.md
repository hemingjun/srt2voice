# SRT2Voice - 智能字幕转语音工具

将SRT字幕文件转换为自然流畅的语音，支持中英文混合内容。

## 特性

- 🎯 **简单易用** - 一行命令即可转换
- 🌍 **中英文混合** - 自动识别并正确发音
- 🎤 **多种音色** - 6种OpenAI高质量语音可选
- 📦 **批量处理** - 支持同时处理多个文件
- ⚙️ **灵活配置** - 可自定义语速、音色等参数
- 💰 **费用透明** - 实时显示处理费用

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/srt2voice.git
cd srt2voice

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt
```

### 配置

首次使用需要配置OpenAI API密钥：

```bash
python -m srt2voice --setup
```

### 使用

```bash
# 转换单个文件
python -m srt2voice input.srt

# 指定输出文件名
python -m srt2voice input.srt -o output.mp3

# 批量处理
python -m srt2voice *.srt --batch

# 使用特定语音
python -m srt2voice input.srt --voice nova

# 调整语速
python -m srt2voice input.srt --speed 0.9
```

## 可用语音

- **alloy** - 中性、平衡的声音（默认）
- **echo** - 温暖、友好的声音
- **fable** - 富有表现力的英式声音
- **onyx** - 深沉、成熟的声音
- **nova** - 充满活力的声音
- **shimmer** - 温柔、舒缓的声音

## 场景预设

```bash
# 教育内容（清晰、稍慢）
python -m srt2voice input.srt --preset educational

# 故事讲述（富有感情）
python -m srt2voice input.srt --preset storytelling

# 专业内容（标准、严谨）
python -m srt2voice input.srt --preset professional
```

## 配置文件

配置文件位于 `~/.srt2voice/config.yaml`，支持以下配置：

```yaml
api:
  openai_key: "your-api-key"

voice:
  default: "alloy"
  speed: 1.0
  model: "tts-1-hd"

output:
  format: "mp3"
  bitrate: "128k"
```

## 费用说明

- **tts-1**: $0.015 / 1000字符
- **tts-1-hd**: $0.030 / 1000字符（高质量，推荐）

10分钟的视频字幕（约2000-3000字）成本约 $0.06-$0.09。

## 常见问题

### 1. 如何处理中英文混合内容？
OpenAI TTS会自动识别并正确处理中英文混合内容，无需特殊设置。

### 2. 音频时长与字幕时间不匹配怎么办？
工具会自动进行时间对齐，允许5-10%的偏差。如果偏差过大，会在日志中显示警告。

### 3. 支持哪些音频格式？
默认输出MP3格式，也支持WAV等其他格式。

### 4. 如何降低费用？
可以使用 `tts-1` 模型代替 `tts-1-hd`，费用降低50%，但音质会有所下降。

## 开发

```bash
# 运行测试
python -m pytest tests/

# 代码格式化
black srt2voice/

# 类型检查
mypy srt2voice/
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 作者

- 您的名字 (@yourusername)

## 鸣谢

- OpenAI - 提供高质量的TTS服务
- pydub - 音频处理
- click - 命令行框架