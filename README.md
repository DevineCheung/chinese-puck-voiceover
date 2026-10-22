# chinese-puck-voiceover

一个给 AI Agent 用的 skill：用 **Puck** 音色把中文科普/解说文稿配成旁白，按章节出 WAV，再拼接、响度标准化，交付整轨 + 分章节 ZIP。

原作在 Manus 环境里写成（依赖 Manus 的 `generate_speech` 工具和 `tts-prompter` skill）。

## 结构

```
chinese-puck-voiceover/
├── SKILL.md                      # 主流程：6 步工作流 + 文稿处理规则
├── references/puck-profile.md    # 音色与表演参数（语速、停顿、响度）
└── scripts/assemble_voiceover.py # 后期脚本：转码、插间隔、拼接、两遍 loudnorm、出 ZIP
```

## 工作流（SKILL.md）

1. **读稿分段**：口播原文一字不改；去掉标题、小节名、方括号舞台提示、括号注音。
2. **规划章节**：按自然章节切分，每段一次 TTS 调用、一个 WAV；品牌结尾单独一轨。
3. **统一合成**：`voice_name: Puck`、`language_code: zh-CN`，`style` 用简短英文（如 `warm, clear, curious, moderately brisk`），全系列保持一致。
4. **省钱恢复**：生成中断后先看输出文件是否已在，不重复调用、不整篇重跑。
5. **后期校验**：48 kHz / 单声道 / 16-bit，章节间隔 0.35 s，目标 -18.1 LUFS、真峰值 ≤ -1.5 dBTP；不变速、不变调、不加混响和音乐。
6. **交付**：整轨 WAV + 分章节 ZIP，报告时长和格式，有遗漏要说明。

## 音色设定（puck-profile.md）

- 年轻男声、温暖、清晰、好奇，"朋友式讲解"，不是播音腔也不是广告腔。
- 语速约 280–310 字/分钟；讲概念、结论、法律风险时放慢。
- 停顿：短 0.2–0.4 s，段落 0.6–0.9 s，重要提问约 1 s（只作参考，精确间隔交给后期）。
- 明确说明：音色名不是模型名，不能保证跨会话完全一致。

## 后期脚本

```bash
python scripts/assemble_voiceover.py \
  --input-dir ./tracks \
  --files 01_opening.wav 02_chapter.wav 03_outro.wav \
  --output out/full.wav --zip out/chapters.zip
```

需要 `ffmpeg` / `ffprobe`。流程：各章转 48k 单声道 PCM → 生成静音间隔 → concat → loudnorm 两遍（线性模式）→ 若真峰值超标，按小步整体降音量（最多 4 次）→ 打印时长、格式、实测响度。只做后期，不生成语音或音乐。

## 简评

- **好用的地方**：后期脚本独立、确定性强，任何 TTS 出的章节 WAV 都能直接用；"不改原文""失败先查文件再重试"这两条规矩很实用。
- **局限**：合成环节绑定 Manus 的 `generate_speech` 和 Puck 音色（Puck 是 Google Gemini TTS 的预置音色之一），换平台要改第 3 步的调用方式；`style` 参数的写法也是按 Manus 接口定的。
- **可以改进**：加一个章节 manifest 文件格式；loudnorm 后用真峰值限幅器替代反复降音量；补一份示例文稿。
