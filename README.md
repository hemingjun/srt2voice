# SRT2Speech

将SRT字幕文件转换为语音音频的Python工具。

## 功能特性

- 支持标准SRT字幕格式
- 多TTS服务支持：
  - **GPT-SoVITS**（本地部署，支持声音克隆）
  - Google TTS
  - Azure TTS（预留）
- 自动服务降级机制
- 情感控制系统
- 音频流畅度优化
- 进度实时显示
- 配置文件支持

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/srt2speech.git
cd srt2speech

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装项目
pip install -e .
```

## 使用方法

### 基本用法

```bash
# 基本使用（默认使用配置中优先级最高的服务）
srt2speech input.srt -o output.wav

# 指定TTS服务
srt2speech input.srt -o output.wav --service google
srt2speech input.srt -o output.wav --service gpt_sovits

# 使用配置文件
srt2speech input.srt -o output.wav --config config/custom.yaml

# 预览模式（只处理前5条字幕）
srt2speech input.srt -o output.wav --preview 5

# 调试模式
srt2speech input.srt -o output.wav --debug
```

### 使用GPT-SoVITS

1. **启动GPT-SoVITS服务**
   ```bash
   cd /path/to/GPT-SoVITS
   python api_v2.py -a 127.0.0.1 -p 9880
   ```

2. **准备参考音频**
   - 录制或准备一段3-10秒的清晰语音作为参考音频
   - 确保音频质量良好，无背景噪音
   - 准备对应的文本内容

3. **配置服务**
   ```bash
   # 复制默认配置作为自定义配置
   cp config/default.yaml config/my_config.yaml
   # 编辑配置文件，设置参考音频路径和文本
   ```

4. **运行转换**
   ```bash
   srt2speech input.srt -o output.wav --config config/my_config.yaml
   ```

## 配置

### 配置文件结构

在`config/default.yaml`中配置默认参数：

```yaml
services:
  gpt_sovits:
    service_name: gpt_sovits
    priority: 1  # 优先级（数字越小越高）
    enabled: true
    credentials:
      api_url: "http://127.0.0.1:9880"
      api_version: "v2"
    voice_settings:
      language: "zh"
      ref_audio_path: "reference.wav"
      prompt_text: "参考音频文本"
      # 更多参数见 config/default.yaml
  
  google:
    service_name: google
    priority: 2
    enabled: true
    credentials:
      key_file: "path/to/google-credentials.json"
    voice_settings:
      language: "zh-CN"
      gender: "FEMALE"
```

### 环境变量

支持通过环境变量配置敏感信息：
- `GOOGLE_APPLICATION_CREDENTIALS`: Google Cloud 认证文件路径
- `AZURE_SPEECH_KEY`: Azure Speech 服务密钥
- `AZURE_SPEECH_REGION`: Azure Speech 服务区域

## 测试

```bash
# 测试GPT-SoVITS连接
python tests/test_gptsovits.py

# 运行所有测试
pytest tests/
```

## 故障排除

### GPT-SoVITS相关问题

1. **连接失败**
   - 确认GPT-SoVITS服务已启动
   - 检查端口是否正确（默认9880）
   - 检查防火墙设置

2. **生成质量问题**
   - 使用高质量的参考音频
   - 调整temperature参数（建议0.3-0.7）
   - 确保参考音频文本准确匹配

3. **性能问题**
   - 使用GPU加速（在GPT-SoVITS配置中设置）
   - 减小batch_size
   - 启用流式模式处理长文本

## 开发状态

- ✅ 第一阶段：基础框架搭建（已完成）
- 🚧 第二阶段：MVP完成 - GPT-SoVITS集成（已完成）
- ⏳ 第三阶段：核心功能完善（进行中）

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License