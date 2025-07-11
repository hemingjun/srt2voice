"""
命令行接口模块
提供用户交互的命令行界面
"""

import click
from pathlib import Path
from datetime import datetime
import sys
import glob as glob_module
from typing import Optional

from .parser import SRTParser
from .tts import TTSGenerator
from .audio import AudioProcessor
from .config import ConfigManager
from .utils import log_progress, format_time, format_size, validate_file_path


@click.command()
@click.argument('input_files', nargs=-1, type=click.Path(exists=True))
@click.option('-o', '--output', help='输出文件名（单文件模式）')
@click.option('--voice', help='语音选择 (alloy/echo/fable/onyx/nova/shimmer)')
@click.option('--speed', type=float, help='语速 (0.25-4.0)')
@click.option('--config', 'config_path', type=click.Path(exists=True), help='配置文件路径')
@click.option('--batch', is_flag=True, help='批量处理模式')
@click.option('--pattern', default='*.srt', help='批量模式的文件匹配模式')
@click.option('--setup', is_flag=True, help='运行配置向导')
@click.option('--show-config', is_flag=True, help='显示当前配置')
@click.option('--preset', help='使用场景预设 (general/educational/storytelling/professional)')
def main(input_files, output, voice, speed, config_path, batch, pattern, setup, show_config, preset):
    """
    SRT2Voice - 智能字幕转语音工具
    
    将SRT字幕文件转换为自然流畅的语音，支持中英文混合。
    
    使用示例:
    
        # 转换单个文件
        srt2voice input.srt
        
        # 批量处理
        srt2voice *.srt --batch
        
        # 使用特定语音
        srt2voice input.srt --voice nova
    """
    
    # 运行配置向导
    if setup:
        ConfigManager.setup_config()
        return
    
    # 加载配置
    try:
        config = ConfigManager(config_path)
    except Exception as e:
        log_progress(f"配置加载失败: {e}", "ERROR")
        sys.exit(1)
    
    # 显示配置
    if show_config:
        show_current_config(config)
        return
    
    # 检查API密钥
    if not config.get('api.openai_key'):
        log_progress("错误：未找到API密钥", "ERROR")
        log_progress("请先运行: srt2voice --setup", "ERROR")
        sys.exit(1)
    
    # 应用命令行参数覆盖
    if voice:
        config.set('voice.default', voice)
    if speed:
        config.set('voice.speed', speed)
    if preset:
        apply_preset(config, preset)
    
    # 确定要处理的文件
    files_to_process = []
    
    if input_files:
        # 处理命令行指定的文件
        files_to_process = list(input_files)
    elif batch:
        # 批量模式，使用pattern匹配文件
        files_to_process = glob_module.glob(pattern)
        if not files_to_process:
            log_progress(f"没有找到匹配 '{pattern}' 的文件", "WARN")
            sys.exit(0)
    else:
        # 没有指定文件
        log_progress("请指定要处理的SRT文件", "ERROR")
        log_progress("使用 srt2voice --help 查看帮助", "INFO")
        sys.exit(1)
    
    # 过滤出SRT文件
    srt_files = [f for f in files_to_process if f.lower().endswith('.srt')]
    
    if not srt_files:
        log_progress("没有找到SRT文件", "ERROR")
        sys.exit(1)
    
    # 单文件模式还是批量模式
    if len(srt_files) == 1 and not batch:
        # 单文件模式
        process_single_file(srt_files[0], output, config)
    else:
        # 批量模式
        process_batch_files(srt_files, config)


def process_single_file(input_file: str, output_file: Optional[str], config: ConfigManager):
    """处理单个文件"""
    try:
        log_progress(f"正在处理: {input_file}")
        
        # 解析SRT文件
        parser = SRTParser(input_file)
        parser.validate()
        subtitles = parser.parse()
        
        total_duration = parser.get_total_duration()
        char_count = parser.get_character_count()
        
        log_progress(f"解析完成，共{len(subtitles)}条字幕")
        log_progress(f"总时长: {format_time(total_duration)}, 总字符数: {char_count}")
        
        # 估算费用
        tts = TTSGenerator(config.get('api.openai_key'), config.get('voice.model'))
        estimated_cost = tts.estimate_cost(char_count)
        log_progress(f"预估费用: ${estimated_cost:.4f}")
        
        # 生成语音
        log_progress("正在生成语音...")
        audio_processor = AudioProcessor()
        
        voice = config.get('voice.default')
        speed = config.get('voice.speed')
        
        total_cost = 0
        for i, sub in enumerate(subtitles):
            # 显示进度
            progress = f"处理进度: {i+1}/{len(subtitles)} ({(i+1)/len(subtitles)*100:.1f}%)"
            log_progress(progress, end='\r')
            
            # 生成语音
            audio_data, cost = tts.generate_speech(sub['text'], voice, speed)
            audio_processor.add_segment(audio_data, sub['start'], sub['end'], sub['text'])
            total_cost += cost
        
        log_progress("")  # 换行
        log_progress("正在合成音频...")
        
        # 确定输出文件名
        if not output_file:
            base_name = Path(input_file).stem
            output_file = f"{base_name}.mp3"
        
        # 导出音频
        audio_processor.export(
            output_file,
            format=config.get('output.format'),
            bitrate=config.get('output.bitrate')
        )
        
        # 获取文件大小
        output_size = Path(output_file).stat().st_size
        
        # 显示结果
        log_progress(f"处理完成: {output_file}")
        log_progress(f"文件大小: {format_size(output_size)}")
        log_progress(f"本次处理费用: ${total_cost:.4f}")
        
    except Exception as e:
        log_progress(f"处理失败: {e}", "ERROR")
        sys.exit(1)


def process_batch_files(srt_files: list, config: ConfigManager):
    """批量处理文件"""
    log_progress(f"找到{len(srt_files)}个SRT文件")
    
    total_cost = 0
    success_count = 0
    failed_files = []
    
    for i, file in enumerate(srt_files, 1):
        log_progress(f"\n[{i}/{len(srt_files)}] 正在处理: {file}")
        
        try:
            # 生成输出文件名（添加时间戳）
            base_name = Path(file).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{base_name}_{timestamp}.mp3"
            
            # 处理文件
            process_file_internal(file, output_file, config)
            
            success_count += 1
            
        except Exception as e:
            log_progress(f"[{i}/{len(srt_files)}] 处理失败: {file} - {e}", "ERROR")
            failed_files.append(file)
    
    # 显示汇总信息
    log_progress("\n" + "="*50)
    log_progress(f"批量处理完成!")
    log_progress(f"成功: {success_count}/{len(srt_files)}")
    
    if failed_files:
        log_progress(f"失败文件列表:", "WARN")
        for file in failed_files:
            log_progress(f"  - {file}", "WARN")


def process_file_internal(input_file: str, output_file: str, config: ConfigManager) -> float:
    """内部文件处理函数（用于批量处理）"""
    # 解析SRT文件
    parser = SRTParser(input_file)
    subtitles = parser.parse()
    
    # 生成语音
    tts = TTSGenerator(config.get('api.openai_key'), config.get('voice.model'))
    audio_processor = AudioProcessor()
    
    voice = config.get('voice.default')
    speed = config.get('voice.speed')
    
    total_cost = 0
    for sub in subtitles:
        audio_data, cost = tts.generate_speech(sub['text'], voice, speed)
        audio_processor.add_segment(audio_data, sub['start'], sub['end'])
        total_cost += cost
    
    # 导出音频
    audio_processor.export(
        output_file,
        format=config.get('output.format'),
        bitrate=config.get('output.bitrate')
    )
    
    log_progress(f"  ✓ 输出: {output_file} (费用: ${total_cost:.4f})")
    
    return total_cost


def apply_preset(config: ConfigManager, preset: str):
    """应用场景预设"""
    presets = {
        'general': {
            'voice.default': 'alloy',
            'voice.speed': 1.0
        },
        'educational': {
            'voice.default': 'nova',
            'voice.speed': 0.95
        },
        'storytelling': {
            'voice.default': 'fable',
            'voice.speed': 0.9
        },
        'professional': {
            'voice.default': 'onyx',
            'voice.speed': 1.0
        }
    }
    
    if preset not in presets:
        log_progress(f"未知的预设: {preset}", "WARN")
        return
    
    # 应用预设配置
    for key, value in presets[preset].items():
        config.set(key, value)
    
    log_progress(f"已应用预设: {preset}")


def show_current_config(config: ConfigManager):
    """显示当前配置"""
    click.echo("=== 当前配置 ===")
    click.echo(f"API密钥: {'已配置' if config.get('api.openai_key') else '未配置'}")
    click.echo(f"默认语音: {config.get('voice.default')}")
    click.echo(f"语速: {config.get('voice.speed')}")
    click.echo(f"TTS模型: {config.get('voice.model')}")
    click.echo(f"输出格式: {config.get('output.format')}")
    click.echo(f"比特率: {config.get('output.bitrate')}")


if __name__ == "__main__":
    main()