#!/usr/bin/env python
"""测试配置映射是否正确工作"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import ConfigManager

def test_config_mapping():
    """测试配置映射"""
    # 加载配置
    config_manager = ConfigManager('config/default.yaml')
    gpt_sovits_config = config_manager.config.services['gpt_sovits'].model_dump()
    
    print("=== GPT-SoVITS 配置映射测试 ===")
    print("\n原始配置数据:")
    import json
    print(json.dumps(gpt_sovits_config, indent=2, ensure_ascii=False))
    
    # 检查连接配置
    print("\n1. 连接配置:")
    connection = gpt_sovits_config.get('connection', {})
    print(f"   - host: {connection.get('host', '未设置')}")
    print(f"   - port: {connection.get('port', '未设置')}")
    print(f"   - timeout: {connection.get('timeout', '未设置')}")
    print(f"   - health_check_timeout: {connection.get('health_check_timeout', '未设置')}")
    print(f"   - max_retries: {connection.get('max_retries', '未设置')}")
    
    # 检查重试策略
    print("\n2. 重试策略:")
    retry = gpt_sovits_config.get('retry_strategy', {})
    print(f"   - initial_delay: {retry.get('initial_delay', '未设置')}")
    print(f"   - max_delay: {retry.get('max_delay', '未设置')}")
    print(f"   - connection_retry_delay: {retry.get('connection_retry_delay', '未设置')}")
    
    # 检查运行时配置
    print("\n3. 运行时配置:")
    runtime = gpt_sovits_config.get('runtime', {})
    print(f"   - python_path: {runtime.get('python_path', '未设置')}")
    print(f"   - fallback_python: {runtime.get('fallback_python', '未设置')}")
    print(f"   - api_script_v1: {runtime.get('api_script_v1', '未设置')}")
    print(f"   - api_script_v2: {runtime.get('api_script_v2', '未设置')}")
    print(f"   - config_file: {runtime.get('config_file', '未设置')}")
    print(f"   - shutdown_wait: {runtime.get('shutdown_wait', '未设置')}")
    
    # 检查音频配置
    print("\n4. 音频配置:")
    audio = gpt_sovits_config.get('audio', {})
    print(f"   - silence_duration: {audio.get('silence_duration', '未设置')}")
    
    # 检查API URL解析
    print("\n5. API URL解析:")
    api_url = gpt_sovits_config['credentials']['api_url']
    print(f"   - 完整URL: {api_url}")
    
    # 验证是否所有值都被正确加载
    print("\n=== 验证结果 ===")
    all_ok = True
    
    if not connection:
        print("❌ 连接配置未加载")
        all_ok = False
    elif all(key in connection for key in ['host', 'port', 'timeout', 'health_check_timeout', 'max_retries']):
        print("✅ 连接配置加载成功")
    else:
        print("⚠️ 连接配置部分缺失")
        all_ok = False
        
    if not retry:
        print("❌ 重试策略未加载")
        all_ok = False
    elif all(key in retry for key in ['initial_delay', 'max_delay', 'connection_retry_delay']):
        print("✅ 重试策略加载成功")
    else:
        print("⚠️ 重试策略部分缺失")
        all_ok = False
        
    if not runtime:
        print("❌ 运行时配置未加载")
        all_ok = False
    elif all(key in runtime for key in ['python_path', 'fallback_python', 'api_script_v1', 'api_script_v2']):
        print("✅ 运行时配置加载成功")
    else:
        print("⚠️ 运行时配置部分缺失")
        all_ok = False
        
    if not audio:
        print("❌ 音频配置未加载")
        all_ok = False
    elif 'silence_duration' in audio:
        print("✅ 音频配置加载成功")
    else:
        print("⚠️ 音频配置部分缺失")
        all_ok = False
    
    print("\n" + "="*40)
    if all_ok:
        print("✅ 所有配置映射正常！")
    else:
        print("❌ 部分配置映射存在问题，请检查配置文件。")
    
    return all_ok

if __name__ == "__main__":
    test_config_mapping()