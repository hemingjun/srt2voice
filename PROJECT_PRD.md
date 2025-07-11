# SRT转语音工具 - 产品需求文档(PRD)

## 快速概览
- **目标**：将SRT字幕转换为自然流畅的语音
- **用户**：个人内容创作者（小白用户）
- **平台**：macOS命令行工具
- **技术**：Python + OpenAI TTS
- **特点**：音质优先，操作简单，支持中英文混合，场景可配置

## 1. 项目概述

### 1.1 项目名称
SRT2Voice - 智能字幕转语音工具

### 1.2 项目目标
开发一个Mac平台的命令行工具，将SRT字幕文件转换为自然流畅的语音音频，适用于各种内容创作场景。

### 1.3 核心价值
- **音质优先**：生成接近真人朗读的自然语音
- **操作简单**：小白用户一键转换
- **灵活通用**：支持多种使用场景配置
- **专业可靠**：准确处理各类专业术语

## 2. 用户画像与场景

### 2.1 目标用户
- 个人内容创作者
- 技术水平：小白用户
- 使用环境：Mac系统
- 使用频率：每周10-20个文件

### 2.2 典型使用场景
1. 用户准备了某个主题的SRT字幕文件
2. 在终端运行命令：`srt2voice input.srt`
3. 等待处理（接受云端延迟）
4. 获得自然流畅的语音文件

### 2.3 文件特征
- 时长：大部分10分钟以内，最长不超过20分钟
- 内容：各类主题内容，可能包含中英文混合
- 格式：标准SRT格式

## 3. 功能需求

### 3.1 核心功能

#### 3.1.1 SRT文件解析
- 支持标准SRT格式
- 自动识别文件编码（UTF-8/GBK）
- 提取时间轴和文本内容
- 验证文件完整性

#### 3.1.2 文本预处理
- 清理特殊字符和标签
- 标准化标点符号
- **保持原文语言**：英文按英文读，中文按中文读
- 不做任何术语转换

#### 3.1.3 语音生成（OpenAI TTS）
- 使用OpenAI TTS API
- **模型选择**：默认使用tts-1-hd（高质量版本）
- 支持6种音色：alloy/echo/fable/onyx/nova/shimmer
- 保持批量处理音色一致
- 自动处理中英文混合内容

#### 3.1.4 时间对齐策略
- **原则**：保持自然语速，允许时长偏差
- **策略**：
  - 不强制加速或截断
  - 通过调整片段间隔适应时间差异
  - 允许总时长有5-10%的偏差

#### 3.1.5 音频输出
- 格式：MP3（默认）或WAV
- 比特率：128kbps（可配置）
- 采样率：44.1kHz
- 单声道输出

#### 3.1.6 特殊需求处理
- **专有名词**：通过配置文件定义需要保护的专业术语
- **多语言**：自动识别中英文，未来可扩展其他语言
- **批量处理**：保持音色一致性
- **场景适配**：通过配置预设适应不同使用场景

### 3.2 用户界面

#### 3.2.1 命令行接口
```bash
# 最简单用法
srt2voice input.srt

# 指定输出文件
srt2voice input.srt -o output.mp3

# 批量处理（自动添加时间戳）
srt2voice *.srt --batch

# 使用特定配置文件
srt2voice input.srt --config custom.yaml

# 临时覆盖配置
srt2voice input.srt --voice nova --speed 1.2

# 使用场景预设
srt2voice input.srt --preset educational

# 初始化配置
srt2voice --config

# 查看当前配置
srt2voice --show-config
```

#### 3.2.2 配置文件
```yaml
# ~/.srt2voice/config.yaml
api:
  openai_key: "your-api-key"
  
voice:
  default: "alloy"  # 默认音色(alloy/echo/fable/onyx/nova/shimmer)
  speed: 1.0       # 语速(0.25-4.0)
  model: "tts-1-hd" # TTS模型(tts-1或tts-1-hd)

output:
  format: "mp3"    # 输出格式
  bitrate: "128k"  # 比特率
  directory: "./"  # 默认输出目录

processing:
  # 文本预处理规则
  text_rules:
    # 是否转换数字为中文
    convert_numbers: false
    # 是否标准化标点
    normalize_punctuation: true
    # 自定义替换规则（可选）
    replacements:
      # - pattern: "regex"
      #   replacement: "text"
  
  # 专业术语保护（可选）
  # 这些词汇将保持原样发音
  preserve_terms:
    # - "Masters"
    # - "birdie"
    # - "专业术语"
  
  # 场景预设（可选）
  # 影响语音的风格和语调
  scene_preset: "general"  # general/educational/storytelling/professional
```

### 3.4 场景预设系统

#### 3.4.1 内置预设
- **general**：通用场景，平衡的参数设置
- **educational**：教育内容，清晰度优先，语速稍慢
- **storytelling**：故事讲述，富有感情，节奏变化
- **professional**：专业内容，准确严谨，标准语速

#### 3.4.2 预设参数示例
```python
SCENE_PRESETS = {
    'general': {
        'voice': 'alloy',
        'speed': 1.0,
        'sentence_pause': 0.5
    },
    'educational': {
        'voice': 'nova',
        'speed': 0.95,
        'sentence_pause': 0.8,
        'optimize_clarity': True
    },
    'storytelling': {
        'voice': 'fable',
        'speed': 0.9,
        'dynamic_pacing': True
    },
    'professional': {
        'voice': 'onyx',
        'speed': 1.0,
        'preserve_technical_terms': True
    }
}
```

#### 3.4.3 自定义预设
用户可以在配置文件中定义自己的预设：
```yaml
custom_presets:
  my_style:
    voice: "echo"
    speed: 1.1
    special_rules:
      - xxx
```

#### 3.3.1 易用性
- 安装：一行命令完成
- 配置：首次运行自动引导
- 使用：默认参数满足90%场景
- 帮助：清晰的错误提示

#### 3.3.2 性能要求
- 10分钟音频处理时间 < 5分钟
- 支持断点续传
- 批量处理支持并发

#### 3.3.3 可靠性
- 网络错误自动重试
- 处理失败保存进度
- 详细的错误日志

## 4. 技术架构

### 4.1 技术栈
- 语言：Python 3.9+
- 主要依赖：
  - openai：官方SDK
  - pydub：音频处理
  - click：命令行框架
  - pysrt：SRT解析
  - tqdm：进度显示

### 4.2 模块设计

```
srt2voice/
├── __main__.py          # 入口
├── cli.py              # 命令行接口
├── parser.py           # SRT解析模块
├── preprocessor.py     # 文本预处理
├── tts.py              # OpenAI TTS封装
├── audio/
│   ├── __init__.py
│   ├── processor.py    # 音频处理
│   └── aligner.py      # 时间对齐
├── config.py           # 配置管理
└── utils/
    ├── __init__.py
    ├── logger.py       # 日志
    └── progress.py     # 进度显示
```

### 4.3 核心流程

```python
# 伪代码示例
def process_srt(srt_file):
    # 1. 解析SRT
    subtitles = parse_srt(srt_file)
    
    # 2. 预处理文本
    for sub in subtitles:
        sub.text = preprocess_text(sub.text)
    
    # 3. 生成语音
    audio_segments = []
    for sub in subtitles:
        audio = generate_tts(sub.text)
        audio_segments.append({
            'audio': audio,
            'start': sub.start,
            'end': sub.end
        })
    
    # 4. 时间对齐
    aligned_audio = align_audio_segments(audio_segments)
    
    # 5. 输出文件
    export_audio(aligned_audio, output_file)
```

## 5. 数据模型

### 5.1 字幕数据结构
```python
class Subtitle:
    index: int           # 序号
    start_time: float    # 开始时间（秒）
    end_time: float      # 结束时间（秒）
    text: str           # 文本内容
    duration: float     # 持续时间
    
class SubtitleFile:
    subtitles: List[Subtitle]
    total_duration: float
    encoding: str
```

### 5.2 音频段数据结构
```python
class AudioSegment:
    audio_data: bytes    # 音频数据
    duration: float      # 实际时长
    target_start: float  # 目标开始时间
    target_end: float    # 目标结束时间
    text: str           # 对应文本
```

## 6. 关键算法

### 6.1 时间对齐算法
```python
def align_segments(segments):
    """
    保持自然语速的时间对齐算法
    """
    aligned = []
    current_time = 0
    
    for segment in segments:
        # 计算理想间隔
        ideal_gap = segment.target_start - current_time
        
        # 添加静音
        if ideal_gap > 0:
            silence = generate_silence(ideal_gap)
            aligned.append(silence)
        
        # 添加音频
        aligned.append(segment.audio_data)
        current_time = segment.target_start + segment.duration
    
    return concatenate_audio(aligned)
```

### 6.2 文件命名规则
```python
def get_output_filename(input_file, is_batch=False):
    """生成输出文件名"""
    base_name = Path(input_file).stem
    
    if is_batch:
        # 批量处理添加时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.mp3"
    else:
        # 单文件处理使用原名
        return f"{base_name}.mp3"
```

### 6.3 进度显示实现
```python
def log_progress(message, level="INFO"):
    """简单日志输出"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

# 使用示例
log_progress("正在处理: input.srt")
log_progress(f"解析完成，共{len(subtitles)}条字幕")
log_progress("正在生成语音...")
log_progress("处理完成: output.mp3")
```

### 6.4 文本预处理规则
```python
def preprocess_text(text, config):
    """根据配置预处理文本"""
    # 1. 清理基础格式
    text = clean_html_tags(text)
    text = remove_extra_spaces(text)
    
    # 2. 应用配置规则
    if config.get('normalize_punctuation'):
        text = normalize_punctuation(text)
    
    # 3. 应用自定义替换
    for rule in config.get('replacements', []):
        text = re.sub(rule['pattern'], rule['replacement'], text)
    
    # 4. 保护专业术语
    for term in config.get('preserve_terms', []):
        # 标记保护词汇，避免被其他处理影响
        text = protect_term(text, term)
    
    return text
```

### 6.5 配置加载机制
```python
def load_config(config_path=None):
    """加载配置，支持多层覆盖"""
    # 1. 加载默认配置
    config = load_default_config()
    
    # 2. 加载用户全局配置
    user_config = Path.home() / '.srt2voice' / 'config.yaml'
    if user_config.exists():
        config.update(load_yaml(user_config))
    
    # 3. 加载指定配置文件
    if config_path:
        config.update(load_yaml(config_path))
    
    # 4. 应用命令行参数覆盖
    config.update(get_cli_overrides())
    
    return config
```

## 7. 错误处理

### 7.1 错误类型与处理
| 错误类型 | 处理方式 | 用户提示 |
|---------|---------|----------|
| 文件不存在 | 立即退出 | "找不到文件：{filename}" |
| SRT格式错误 | 显示行号 | "第{line}行格式错误" |
| API密钥无效 | 提示配置 | "错误：未找到API密钥\n请先运行: srt2voice --config" |
| 网络超时 | 自动重试3次 | "网络连接中..." |
| 音频生成失败 | 标记并继续 | "第{index}段生成失败" |

### 7.2 日志级别
- ERROR：必须处理的错误
- WARNING：可能影响质量
- INFO：处理进度
- DEBUG：详细调试信息

## 8. 配置项说明

### 8.1 必需配置
```yaml
api:
  openai_key: ""  # OpenAI API密钥
```

### 8.2 可选配置
```yaml
voice:
  model: "tts-1-hd"      # TTS模型(tts-1或tts-1-hd)
  voice: "alloy"         # 音色选择
  speed: 1.0            # 语速(0.25-4.0)

audio:
  format: "mp3"         # 输出格式
  bitrate: "128k"       # 比特率
  sample_rate: 44100    # 采样率

processing:
  max_retries: 3        # 最大重试次数
  timeout: 30           # 超时时间(秒)
  concurrent: 3         # 并发数
  
  # 高级文本处理选项
  text_processing:
    # 语言检测
    auto_detect_language: true
    # 停顿控制
    sentence_pause: 0.5   # 句子间停顿(秒)
    paragraph_pause: 1.0  # 段落间停顿(秒)
    
  # 场景优化
  optimization:
    # 是否优化长句
    optimize_long_sentences: true
    # 最大句子长度
    max_sentence_length: 50

output:
  directory: "./"       # 输出目录
  naming: "auto"        # 命名规则(auto/custom)
  # 自定义命名模板
  # custom_template: "{name}_{date}_{time}"
```

## 9. 配置示例

### 9.1 默认配置（通用场景）
```yaml
api:
  openai_key: "sk-xxxxx"

voice:
  default: "alloy"
  speed: 1.0
  model: "tts-1-hd"

processing:
  scene_preset: "general"
```

### 9.2 教育内容配置
```yaml
voice:
  default: "nova"      # 清晰明亮的声音
  speed: 0.95         # 稍慢的语速
  
processing:
  scene_preset: "educational"
  text_processing:
    sentence_pause: 0.8
    paragraph_pause: 1.5
```

### 9.3 故事讲述配置
```yaml
voice:
  default: "fable"    # 富有表现力
  speed: 0.9
  
processing:
  scene_preset: "storytelling"
  optimization:
    optimize_long_sentences: true
```

### 9.4 专业内容配置（如高尔夫教程）
```yaml
voice:
  default: "onyx"     # 成熟深沉
  speed: 1.0

processing:
  scene_preset: "professional"
  preserve_terms:
    - "Masters"
    - "birdie"
    - "eagle"
    - "par"
    - "tee"
  text_rules:
    convert_numbers: false  # 保持数字原样
```

## 10. 测试用例

### 10.1 基础功能测试
1. 单文件转换
2. 中英文混合
3. 长时间文件(20分钟)
4. 批量处理
5. 不同配置预设

### 10.2 异常测试
1. 格式错误的SRT
2. 网络中断恢复
3. API限流处理
4. 超大文件处理
5. 配置文件错误

### 10.3 质量验证
1. 音质评估
2. 时间准确度
3. 专业术语发音
4. 不同场景效果

## 11. 版本规划

### 11.1 当前版本 (v1.0)
- 核心SRT转语音功能
- OpenAI TTS集成
- 命令行工具
- 批量处理支持
- 灵活配置系统

### 11.2 可能的未来改进
- 更多语言支持
- 高级音频效果
- GUI界面
- 云端服务
- 更多TTS服务支持

## 12. 交付标准

### 11.1 功能完成度
- [x] SRT解析准确率 > 99%
- [x] 中英文混合支持
- [x] 批量处理功能
- [x] 错误恢复机制

### 11.2 性能指标
- 10分钟文件处理 < 5分钟
- 内存占用 < 500MB
- API调用成功率 > 95%

### 11.3 用户体验
- 安装步骤 ≤ 3步
- 首次使用成功率 > 90%
- 错误提示清晰度 100%

## 12. 开发注意事项

### 12.1 代码规范
- 遵循PEP 8
- 类型注解完整
- 文档字符串规范

### 12.2 安全考虑
- API密钥加密存储
- 输入验证严格
- 临时文件清理

### 12.3 兼容性
- Python 3.9+
- macOS 10.15+
- 支持M1/M2芯片

## 12. 成本估算

### 12.1 OpenAI TTS定价
- **tts-1**: $0.015 / 1000字符
- **tts-1-hd**: $0.030 / 1000字符（高质量版本）

### 12.2 使用成本预估
以10分钟视频为例：
- 平均字数：约2000-3000字
- 使用tts-1-hd：$0.06-$0.09
- 使用tts-1：$0.03-$0.045

### 12.3 月度成本预估
- 每周20个文件 × 4周 = 80个文件/月
- 使用tts-1-hd：约$4.8-$7.2/月
- 完全在可接受范围内

## 13. 实现要点

### 14.1 开发优先级
1. **Phase 1 - 核心功能**（第1周）
   - SRT解析器
   - OpenAI TTS基础调用
   - 简单音频拼接

2. **Phase 2 - 完善体验**（第2周）
   - 配置管理系统
   - 错误处理
   - 日志输出
   - 批量处理

3. **Phase 3 - 优化调试**（第3周）
   - 时间对齐优化
   - 配置预设实现
   - 性能优化
   - 测试完善

### 14.2 关键代码示例

#### 配置初始化
```python
def init_config():
    config_path = Path.home() / '.srt2voice' / 'config.yaml'
    if not config_path.exists():
        print("错误：未找到配置文件")
        print("请先运行: srt2voice --config")
        sys.exit(1)
    return load_config(config_path)
```

#### OpenAI TTS调用
```python
def generate_speech(text, voice="alloy"):
    client = OpenAI(api_key=config['api']['openai_key'])
    response = client.audio.speech.create(
        model="tts-1-hd",
        voice=voice,
        input=text
    )
    return response.content
```

#### 场景预设应用
```python
def apply_scene_preset(config, preset):
    presets = {
        'educational': {
            'speed': 0.95,
            'sentence_pause': 0.8
        },
        'storytelling': {
            'speed': 0.9,
            'optimize_long_sentences': True
        }
    }
    if preset in presets:
        config.update(presets[preset])
```

### 14.3 注意事项
- 所有用户提示使用中文
- 错误信息要具体明确
- 保留原始SRT文本不做转换
- 确保音频连接平滑
- 配置文件要有详细注释

## 15. 使用示例

### 14.1 首次使用
```bash
# 1. 安装工具
pip install srt2voice

# 2. 配置API密钥
srt2voice --config
> 请输入您的OpenAI API密钥: sk-xxxxx
> 配置已保存到: ~/.srt2voice/config.yaml

# 3. 转换单个文件
srt2voice intro.srt
[14:23:15] [INFO] 正在处理: intro.srt
[14:23:15] [INFO] 解析完成，共18条字幕
[14:23:16] [INFO] 正在生成语音...
[14:23:45] [INFO] 生成完成，正在合成音频...
[14:23:47] [INFO] 处理完成: intro.mp3
```

### 14.2 批量处理
```bash
# 批量转换当前目录所有SRT文件
srt2voice *.srt --batch
[14:25:01] [INFO] 找到3个SRT文件
[14:25:01] [INFO] [1/3] 正在处理: chapter1.srt
[14:25:32] [INFO] [1/3] 完成: chapter1_20240120_142532.mp3
[14:25:32] [INFO] [2/3] 正在处理: chapter2.srt
...
```

### 14.3 使用自定义配置
```bash
# 使用特定配置文件
srt2voice input.srt --config custom_config.yaml

# 临时覆盖配置
srt2voice input.srt --voice nova --speed 1.2
```

### 14.4 示例SRT内容
```srt
1
00:00:00,000 --> 00:00:05,000
欢迎来到我们的教程

2
00:00:05,500 --> 00:00:10,000
Today we'll explore something amazing

3
00:00:10,500 --> 00:00:15,000
让我们开始今天的学习之旅
```

---

本PRD版本：1.2
更新日期：2024-01-20
更新内容：增加灵活配置系统，移除场景硬编码
维护者：[您的名字]