#!/usr/bin/env python3
"""管理GPT-SoVITS参考音频配置"""
import os
import sys
import yaml
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def list_voices():
    """列出所有参考音频配置"""
    voice_dir = Path("config/reference_voices")
    if not voice_dir.exists():
        print("参考音频配置目录不存在")
        return
    
    print("\n可用的参考音频配置：")
    print("-" * 60)
    
    for yaml_file in voice_dir.glob("*.yaml"):
        if yaml_file.name == "README.md":
            continue
            
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            print(f"\n配置文件: {yaml_file.name}")
            print(f"  音色名称: {config.get('voice_name', '未命名')}")
            print(f"  音频路径: {config.get('ref_audio_path', '未设置')}")
            print(f"  文本内容: {config.get('prompt_text', '未设置')[:30]}...")
            print(f"  语言: {config.get('prompt_lang', 'zh')}")
            if 'description' in config:
                print(f"  描述: {config.get('description')}")
                
        except Exception as e:
            print(f"  读取失败: {e}")


def create_voice(name, audio_path, text, lang='zh', description=''):
    """创建新的参考音频配置"""
    voice_dir = Path("config/reference_voices")
    voice_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名
    filename = name.lower().replace(' ', '_') + '.yaml'
    filepath = voice_dir / filename
    
    # 检查音频文件是否存在
    if not Path(audio_path).exists():
        print(f"错误：音频文件不存在: {audio_path}")
        return False
    
    # 创建配置
    config = {
        'voice_name': name,
        'ref_audio_path': str(Path(audio_path).absolute()),
        'prompt_text': text,
        'prompt_lang': lang,
        'description': description
    }
    
    # 保存配置
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✓ 已创建参考音频配置: {filepath}")
    return True


def update_main_config(voice_config_name):
    """更新主配置文件使用指定的参考音频"""
    voice_file = Path(f"config/reference_voices/{voice_config_name}")
    if not voice_file.exists():
        voice_file = Path(f"config/reference_voices/{voice_config_name}.yaml")
    
    if not voice_file.exists():
        print(f"错误：找不到配置文件: {voice_config_name}")
        return False
    
    # 读取参考音频配置
    with open(voice_file, 'r', encoding='utf-8') as f:
        voice_config = yaml.safe_load(f)
    
    # 更新默认配置
    example_config = Path("config/default.yaml")
    if example_config.exists():
        with open(example_config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 更新voice_settings
        config['services']['gpt_sovits']['voice_settings'].update({
            'ref_audio_path': voice_config['ref_audio_path'],
            'prompt_text': voice_config['prompt_text'],
            'prompt_lang': voice_config.get('prompt_lang', 'zh')
        })
        
        # 保存更新
        with open(example_config, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"✓ 已更新配置文件使用: {voice_config['voice_name']}")
        return True
    
    return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='管理GPT-SoVITS参考音频配置')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list命令
    subparsers.add_parser('list', help='列出所有参考音频配置')
    
    # create命令
    create_parser = subparsers.add_parser('create', help='创建新的参考音频配置')
    create_parser.add_argument('name', help='音色名称')
    create_parser.add_argument('audio_path', help='音频文件路径')
    create_parser.add_argument('text', help='音频对应的文本内容')
    create_parser.add_argument('--lang', default='zh', help='语言代码（默认zh）')
    create_parser.add_argument('--desc', default='', help='描述信息')
    
    # use命令
    use_parser = subparsers.add_parser('use', help='使用指定的参考音频配置')
    use_parser.add_argument('config_name', help='配置文件名（不需要.yaml后缀）')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_voices()
    elif args.command == 'create':
        create_voice(args.name, args.audio_path, args.text, args.lang, args.desc)
    elif args.command == 'use':
        update_main_config(args.config_name)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()