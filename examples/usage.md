# srt2speech 使用示例

## 基本使用

### 1. 使用默认配置（自动启动 GPT-SoVITS）
```bash
# 从项目根目录运行
python -m src.cli input.srt

# 或者使用 srt2speech 命令（如果已安装）
srt2speech input.srt
```

### 2. 指定配置文件
```bash
# 使用绝对路径
python -m src.cli input.srt -c /path/to/srt2speech/config/default.yaml

# 使用相对路径（从项目根目录）
python -m src.cli input.srt -c config/default.yaml
```

### 3. 调试模式（查看详细日志）
```bash
python -m src.cli input.srt --debug
```

## 配置文件说明

### 自动启动配置
在 `config/default.yaml` 中：
```yaml
services:
  gpt_sovits:
    auto_start:
      enabled: true  # 设置为 true 启用自动启动
      gpt_sovits_path: "/path/to/your/GPT-SoVITS"  # 设置为您的 GPT-SoVITS 项目路径
```

### 手动启动 GPT-SoVITS
如果不想使用自动启动，可以：
1. 将 `auto_start.enabled` 设置为 `false`
2. 手动启动服务：
```bash
cd /path/to/GPT-SoVITS
python api_v2.py -a 127.0.0.1 -p 9880
```

## 故障排除

### 1. 自动启动不工作
- 确认配置文件路径正确
- 确认 `gpt_sovits_path` 指向正确的 GPT-SoVITS 项目目录
- 使用 `--debug` 查看详细日志

### 2. 测试配置
```bash
# 运行配置测试脚本
python test_config.py
```

### 3. 查看可用服务
```bash
python -m src.cli --list-services
```