# SRT2Voice 开发计划书

## 项目概述
- **项目名称**：SRT2Voice - 智能字幕转语音工具
- **开发周期**：3周（15个工作日）
- **开发工具**：Claude Code + Python 3.9+
- **目标**：开发一个通用的SRT转语音命令行工具，支持中英文混合，易于使用

## 开发环境准备

### 必需条件
```bash
# 1. Python环境 (3.9+)
python --version

# 2. 创建项目目录
mkdir srt2voice
cd srt2voice

# 3. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS

# 4. 初始化git仓库
git init
```

### 依赖清单
```txt
# requirements.txt
openai>=1.0.0
pydub>=0.25.1
click>=8.0.0
pysrt>=1.1.2
tqdm>=4.65.0
pyyaml>=6.0
colorama>=0.4.6
```

## 项目结构
```
srt2voice/
├── README.md               # 项目说明
├── setup.py               # 安装配置
├── requirements.txt       # 依赖列表
├── .gitignore            # Git忽略文件
├── srt2voice/            # 主程序包
│   ├── __init__.py       # 包初始化
│   ├── __main__.py       # 程序入口
│   ├── cli.py            # 命令行接口
│   ├── parser.py         # SRT解析器
│   ├── tts.py            # TTS处理
│   ├── audio.py          # 音频处理
│   ├── config.py         # 配置管理
│   └── utils.py          # 工具函数
├── tests/                # 测试目录
│   ├── test_parser.py
│   ├── test_tts.py
│   └── sample.srt        # 测试文件
└── examples/             # 示例文件
    └── config.yaml       # 配置示例
```

## 开发阶段划分

### 第一阶段：核心功能实现（第1-5天）

#### Day 1-2: 基础架构搭建
**任务清单**：
1. 创建项目结构
2. 实现SRT解析器（parser.py）
3. 编写基础测试用例

**parser.py 核心代码**：
```python
import pysrt
from pathlib import Path
from typing import List, Dict

class SRTParser:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.subtitles = []
        
    def parse(self) -> List[Dict]:
        """解析SRT文件"""
        try:
            subs = pysrt.open(self.file_path)
            for sub in subs:
                self.subtitles.append({
                    'index': sub.index,
                    'start': sub.start.ordinal / 1000.0,  # 转换为秒
                    'end': sub.end.ordinal / 1000.0,
                    'text': sub.text.strip(),
                    'duration': (sub.end - sub.start).ordinal / 1000.0
                })
            return self.subtitles
        except Exception as e:
            raise ValueError(f"SRT文件解析失败: {e}")
```

#### Day 3-4: OpenAI TTS集成
**任务清单**：
1. 实现TTS基础调用（tts.py）
2. 处理中英文混合文本
3. 添加费用计算功能

**tts.py 核心代码**：
```python
from openai import OpenAI
import os
from typing import Tuple

class TTSGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.char_count = 0
        self.model = "tts-1-hd"
        self.price_per_1k = 0.030  # $0.030 per 1000 chars
        
    def generate_speech(self, text: str, voice: str = "alloy") -> Tuple[bytes, float]:
        """生成语音并返回音频数据和费用"""
        # 计算字符数
        self.char_count += len(text)
        
        # 调用OpenAI TTS
        response = self.client.audio.speech.create(
            model=self.model,
            voice=voice,
            input=text
        )
        
        # 计算本次费用
        cost = (len(text) / 1000) * self.price_per_1k
        
        return response.content, cost
    
    def get_total_cost(self) -> float:
        """获取总费用"""
        return (self.char_count / 1000) * self.price_per_1k
```

#### Day 5: 音频处理与合成
**任务清单**：
1. 实现音频片段合成（audio.py）
2. 处理时间对齐（允许15%偏差）
3. 支持MP3输出

**audio.py 核心代码**：
```python
from pydub import AudioSegment
from pydub.generators import Sine
import io
from typing import List, Dict

class AudioProcessor:
    def __init__(self):
        self.segments = []
        
    def add_segment(self, audio_data: bytes, start_time: float, end_time: float):
        """添加音频片段"""
        audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
        self.segments.append({
            'audio': audio,
            'start': start_time,
            'end': end_time,
            'duration': len(audio) / 1000.0
        })
    
    def align_and_merge(self) -> AudioSegment:
        """对齐并合并音频"""
        final_audio = AudioSegment.empty()
        current_time = 0
        
        for segment in self.segments:
            # 计算需要的静音时长
            gap = segment['start'] - current_time
            
            # 添加静音（如果需要）
            if gap > 0:
                silence = AudioSegment.silent(duration=gap * 1000)
                final_audio += silence
                current_time += gap
            
            # 添加音频片段
            final_audio += segment['audio']
            current_time = segment['start'] + segment['duration']
        
        return final_audio
    
    def export(self, output_path: str, format: str = "mp3", bitrate: str = "128k"):
        """导出音频文件"""
        audio = self.align_and_merge()
        audio.export(output_path, format=format, bitrate=bitrate)
```

### 第二阶段：完善体验（第6-10天）

#### Day 6-7: 命令行接口
**任务清单**：
1. 实现CLI主命令（cli.py）
2. 添加参数解析
3. 实现简洁的进度显示

**cli.py 核心代码**：
```python
import click
from pathlib import Path
from datetime import datetime
from .parser import SRTParser
from .tts import TTSGenerator
from .audio import AudioProcessor
from .config import ConfigManager
from .utils import log_progress

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', help='输出文件名')
@click.option('--voice', default='alloy', help='语音选择')
@click.option('--config', type=click.Path(), help='配置文件路径')
@click.option('--batch', is_flag=True, help='批量处理模式')
def main(input_file, output, voice, config, batch):
    """SRT转语音工具"""
    # 加载配置
    cfg = ConfigManager(config)
    if not cfg.get('api.openai_key'):
        click.echo("错误：未找到API密钥")
        click.echo("请先运行: srt2voice --setup")
        return
    
    # 处理文件
    process_file(input_file, output, voice, cfg, batch)

def process_file(input_file, output, voice, config, batch):
    """处理单个文件"""
    log_progress(f"正在处理: {input_file}")
    
    # 1. 解析SRT
    parser = SRTParser(input_file)
    subtitles = parser.parse()
    log_progress(f"解析完成，共{len(subtitles)}条字幕")
    
    # 2. 生成语音
    log_progress("正在生成语音...")
    tts = TTSGenerator(config.get('api.openai_key'))
    audio_processor = AudioProcessor()
    
    total_cost = 0
    for i, sub in enumerate(subtitles):
        log_progress(f"处理进度: {i+1}/{len(subtitles)}", end='\r')
        audio_data, cost = tts.generate_speech(sub['text'], voice)
        audio_processor.add_segment(audio_data, sub['start'], sub['end'])
        total_cost += cost
    
    # 3. 合成输出
    log_progress("\n正在合成音频...")
    if not output:
        base_name = Path(input_file).stem
        if batch:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"{base_name}_{timestamp}.mp3"
        else:
            output = f"{base_name}.mp3"
    
    audio_processor.export(output)
    
    # 4. 显示结果
    log_progress(f"处理完成: {output}")
    log_progress(f"本次处理费用: ${total_cost:.4f}")
```

#### Day 8-9: 配置管理系统
**任务清单**：
1. 实现配置文件管理（config.py）
2. 支持首次运行引导
3. 实现配置覆盖机制

**config.py 核心代码**：
```python
import yaml
from pathlib import Path
import click

class ConfigManager:
    def __init__(self, config_path=None):
        self.config = self._load_default()
        self._load_user_config()
        if config_path:
            self._load_file(config_path)
    
    def _load_default(self):
        """默认配置"""
        return {
            'api': {'openai_key': ''},
            'voice': {
                'default': 'alloy',
                'speed': 1.0,
                'model': 'tts-1-hd'
            },
            'output': {
                'format': 'mp3',
                'bitrate': '128k'
            }
        }
    
    def _load_user_config(self):
        """加载用户配置"""
        config_file = Path.home() / '.srt2voice' / 'config.yaml'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                self._merge_config(user_config)
    
    def setup_config(self):
        """配置向导"""
        click.echo("=== SRT2Voice 配置向导 ===")
        api_key = click.prompt("请输入您的OpenAI API密钥", hide_input=True)
        
        config_dir = Path.home() / '.srt2voice'
        config_dir.mkdir(exist_ok=True)
        
        config_data = self._load_default()
        config_data['api']['openai_key'] = api_key
        
        config_file = config_dir / 'config.yaml'
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
        
        click.echo(f"配置已保存到: {config_file}")
```

#### Day 10: 错误处理与日志
**任务清单**：
1. 实现统一错误处理
2. 添加重试机制
3. 完善日志输出

**utils.py 核心代码**：
```python
from datetime import datetime
import time
from functools import wraps

def log_progress(message: str, level: str = "INFO", end='\n'):
    """统一的日志输出"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", end=end)

def retry_on_error(max_retries=3, delay=1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    log_progress(f"请求失败，{delay}秒后重试... ({attempt + 1}/{max_retries})", "WARN")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

class SRT2VoiceError(Exception):
    """自定义异常基类"""
    pass

class ConfigError(SRT2VoiceError):
    """配置错误"""
    pass

class TTSError(SRT2VoiceError):
    """TTS调用错误"""
    pass
```

### 第三阶段：优化与完善（第11-15天）

#### Day 11-12: 批量处理优化
**任务清单**：
1. 实现批量文件处理
2. 添加并发控制
3. 优化内存使用

**批量处理扩展**：
```python
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed

@click.option('--batch', is_flag=True, help='批量处理模式')
@click.option('--pattern', default='*.srt', help='文件匹配模式')
def batch_process(pattern, config):
    """批量处理多个文件"""
    files = glob.glob(pattern)
    log_progress(f"找到{len(files)}个SRT文件")
    
    total_cost = 0
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(process_file, f, None, config, True): f 
            for f in files
        }
        
        for i, future in enumerate(as_completed(futures)):
            file = futures[future]
            try:
                cost = future.result()
                total_cost += cost
                log_progress(f"[{i+1}/{len(files)}] 完成: {file}")
            except Exception as e:
                log_progress(f"[{i+1}/{len(files)}] 失败: {file} - {e}", "ERROR")
    
    log_progress(f"批量处理完成，总费用: ${total_cost:.4f}")
```

#### Day 13: 高级配置功能
**任务清单**：
1. 实现场景预设
2. 添加文本预处理规则
3. 支持专业术语保护

**场景预设实现**：
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
        'sentence_pause': 0.8
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

def apply_preset(config, preset_name):
    """应用场景预设"""
    if preset_name in SCENE_PRESETS:
        preset = SCENE_PRESETS[preset_name]
        for key, value in preset.items():
            config.set(f'voice.{key}', value)
```

#### Day 14: 测试与文档
**任务清单**：
1. 编写单元测试
2. 创建README文档
3. 准备示例文件

**README.md 模板**：
```markdown
# SRT2Voice - 智能字幕转语音工具

将SRT字幕文件转换为自然流畅的语音，支持中英文混合。

## 快速开始

### 安装
\`\`\`bash
git clone https://github.com/yourname/srt2voice.git
cd srt2voice
pip install -r requirements.txt
\`\`\`

### 配置
\`\`\`bash
python -m srt2voice --setup
\`\`\`

### 使用
\`\`\`bash
# 转换单个文件
python -m srt2voice input.srt

# 批量处理
python -m srt2voice *.srt --batch

# 使用特定语音
python -m srt2voice input.srt --voice nova
\`\`\`

## 功能特点
- 支持中英文混合
- 多种语音选择
- 批量处理
- 灵活配置
- 费用统计

## 配置说明
配置文件位置：`~/.srt2voice/config.yaml`

## 常见问题
...
```

#### Day 15: 打包与发布
**任务清单**：
1. 创建setup.py
2. 测试安装流程
3. 准备GitHub发布

**setup.py**：
```python
from setuptools import setup, find_packages

setup(
    name="srt2voice",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "pydub>=0.25.1",
        "click>=8.0.0",
        "pysrt>=1.1.2",
        "tqdm>=4.65.0",
        "pyyaml>=6.0",
        "colorama>=0.4.6"
    ],
    entry_points={
        'console_scripts': [
            'srt2voice=srt2voice.cli:main',
        ],
    },
    author="Your Name",
    description="SRT字幕转语音工具",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourname/srt2voice",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
    ],
    python_requires='>=3.9',
)
```

## 测试计划

### 功能测试清单
1. **基础功能**
   - [ ] 单文件转换
   - [ ] 中文内容
   - [ ] 英文内容
   - [ ] 中英文混合
   - [ ] 长文件（20分钟）

2. **批量处理**
   - [ ] 多文件批量
   - [ ] 文件名时间戳
   - [ ] 并发处理

3. **配置管理**
   - [ ] 首次配置向导
   - [ ] 配置文件读取
   - [ ] 命令行参数覆盖

4. **错误处理**
   - [ ] 无效SRT格式
   - [ ] 网络错误重试
   - [ ] API密钥错误
   - [ ] 文件权限问题

### 性能指标
- 10分钟文件处理时间 < 5分钟
- 内存占用 < 500MB
- API调用成功率 > 95%

## 交付标准

### 完成标志
1. **功能完整**：所有核心功能可用
2. **文档齐全**：README、配置示例、使用说明
3. **测试通过**：基础测试用例全部通过
4. **可安装使用**：pip安装流程正常

### 质量要求
1. **代码规范**：遵循PEP 8
2. **错误提示**：中文提示，清晰明确
3. **用户体验**：3步内完成首次使用

## 开发注意事项

### 给Claude Code的特别提示
1. **逐步实现**：按照阶段计划逐步完成
2. **测试先行**：每个模块都要有基础测试
3. **注释清晰**：关键逻辑添加中文注释
4. **错误处理**：所有外部调用都要有异常处理
5. **进度反馈**：用户操作都要有明确反馈

### 关键技术点
1. **中英文混合**：OpenAI TTS会自动处理，无需特殊处理
2. **时间对齐**：使用静音填充，允许15%偏差
3. **费用计算**：每次调用都要累计，最后汇总显示
4. **配置管理**：支持多层覆盖，命令行参数优先级最高

## 项目里程碑

| 阶段 | 时间 | 交付物 | 验证标准 |
|-----|------|--------|---------|
| 第一阶段 | Day 1-5 | 核心功能原型 | 能够转换简单SRT文件 |
| 第二阶段 | Day 6-10 | 完整功能版本 | 支持配置、批量处理 |
| 第三阶段 | Day 11-15 | 发布版本 | 文档完整、可安装使用 |

## 风险管理

### 技术风险
1. **OpenAI API限制**：建议添加请求频率控制
2. **音频处理性能**：大文件可能需要分段处理
3. **中英文识别**：依赖OpenAI自动处理

### 应对措施
1. 实现请求队列和速率限制
2. 添加流式处理选项
3. 提供手动语言标记选项（未来版本）

---

本计划书版本：1.0
生成日期：2024-01-20
适用于：Claude Code开发执行