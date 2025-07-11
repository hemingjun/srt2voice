# SRT2Speech

将SRT字幕文件转换为语音音频的Python工具。

## 功能特性

- 支持标准SRT字幕格式
- 多TTS服务支持（Google TTS、Azure TTS）
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

```bash
# 基本使用
srt2speech input.srt -o output.wav

# 指定TTS服务
srt2speech input.srt -o output.wav --service google

# 使用配置文件
srt2speech input.srt -o output.wav --config config/custom.yaml

# 预览模式（只处理前5条字幕）
srt2speech input.srt -o output.wav --preview 5

# 调试模式
srt2speech input.srt -o output.wav --debug
```

## 配置

在`config/default.yaml`中配置默认参数和API密钥。

## 开发状态

项目正在积极开发中，第一阶段基础框架正在构建。