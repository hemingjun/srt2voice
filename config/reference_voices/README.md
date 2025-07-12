# 参考音频配置目录

这个目录用于存放不同的参考音频配置文件，方便管理多个声音。

## 使用方法

### 1. 创建新的参考音频配置
   - 复制 `default.yaml` 为新文件，如 `male_voice.yaml`
   - 修改其中的参数

### 2. 配置文件格式
   ```yaml
   voice_name: "音色名称"
   ref_audio_path: "音频文件的绝对路径"
   prompt_text: "音频中说的准确文本内容"
   prompt_lang: "zh"  # 语言代码
   description: "可选的描述信息"
   ```

### 3. 在主配置中使用
   在 `config/default.yaml` 或您的自定义配置文件中，设置 `voice_profile` 字段：
   
   ```yaml
   services:
     gpt_sovits:
       voice_settings:
         voice_profile: "default"  # 使用 default.yaml
         # 或
         voice_profile: "male_voice"  # 使用 male_voice.yaml
   ```

### 4. 动态切换声音
   只需修改配置文件中的 `voice_profile` 值，即可切换到不同的参考音频。
   无需修改其他参数，系统会自动加载对应的音频配置。

## 示例配置

### 男声播音
```yaml
voice_name: "男声播音"
ref_audio_path: "/path/to/male_voice.wav"
prompt_text: "大家好，欢迎收听今天的节目"
prompt_lang: "zh"
description: "成熟稳重的男性播音声音"
```

### 女声旁白
```yaml
voice_name: "女声旁白"
ref_audio_path: "/path/to/female_voice.wav"
prompt_text: "在这个美丽的早晨，让我们一起开始新的一天"
prompt_lang: "zh"
description: "温柔亲切的女性旁白声音"
```

## 注意事项

1. **音频要求**
   - 时长：3-10秒
   - 格式：WAV推荐
   - 质量：清晰无噪音

2. **文本准确性**
   - `prompt_text` 必须与音频内容完全一致
   - 包括标点符号的位置

3. **路径问题**
   - 推荐使用绝对路径
   - 或相对于GPT-SoVITS根目录的路径