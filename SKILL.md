---
name: chinese-puck-voiceover
description: Create and package Mandarin Chinese educational and explainer voiceovers using the user's preferred Puck voice and performance style. Use when a user provides a Chinese narration script, requests Puck narration, chapter-separated WAV tracks, or assembly and loudness mastering of generated speech.
---

# Chinese Puck Voiceover

Create consistent Mandarin educational narration in the user's preferred Puck voice. Read `references/puck-profile.md` when selecting delivery, preparing scripts, or mastering audio. This skill governs narration workflow only; generate or mix background music only when the user explicitly asks.

## Workflow

1. **Read and segment the script.** Preserve the user's spoken wording and factual claims. Remove only clearly non-spoken material such as title labels, section headings, square-bracket stage directions, and parenthetical pronunciation notes when the user says not to read them. Keep opening questions and explicitly marked spoken brand/outro text. Convert performance notes into concise style direction, punctuation, or pause tags; do not place stage directions in spoken text.
2. **Plan chapter tracks.** Split at natural chapter boundaries, keeping each `generate_speech` call within the tool's current character limit. Use one call per planned track and one output WAV per track. Keep a brand outro as its own track when requested. Avoid test generations unless requested; do not regenerate completed clips merely to adjust post-processing.
3. **Synthesize consistently.** Before generation, read the current `tts-prompter` skill and inspect the current `manus-tools.generate_speech` schema. Use `voice_name: Puck`, `language_code: zh-CN`, and a consistent base delivery style across chapters. Put spoken content only in `turns[].text`; use concise English style directions in `turns[].style`. Do not claim a specific underlying model, model version, or seed because the interface does not expose them.
4. **Recover economically.** After any interrupted or failed-looking generation, inspect the expected output paths before retrying. If audio files exist, use them. Do not automatically issue duplicate generation calls or regenerate a full script to repair one missing section; ask before consuming additional credits when the user's authorization or budget is unclear.
5. **Post-process and verify.** Unless the user requests different specs, normalize generated tracks to 48 kHz, mono, 16-bit PCM WAV; connect tracks in script order with a 0.35-second gap; target approximately -18.1 LUFS integrated loudness and keep true peak at or below -1.5 dBTP. Do not time-stretch, pitch-shift, add reverb, or add music unless requested. Use `scripts/assemble_voiceover.py` for deterministic assembly, normalization, validation, and chapter ZIP creation.
6. **Deliver.** Provide a full-length WAV and a ZIP of normalized chapter tracks. State duration, sample rate, channel count, and whether music was included. If any section was omitted, could not be generated, or is only approximate, disclose it plainly.

## Script-to-speech handling

- Read visible prose verbatim unless the user asks for editorial changes.
- Do not speak Markdown headings, title labels, bracketed acting cues, or parenthetical pronunciation guides marked as non-spoken.
- Retain the opening hook, quoted speech, numbers, units, proper nouns, and brand outro if the user identifies them as spoken.
- Use natural punctuation and occasional `<short pause>` / `<long pause>` tags for in-sentence pacing. Treat duration ranges in a script as guidance; verify exact inter-track gaps in post-processing.
- Keep each generation turn short and behaviorally specific. Use the same baseline style string throughout a series; vary a turn's direction only for a clear, sustained delivery change (for example, a cautious legal-risk passage).
- For long scripts, align audio filenames with chapter order and labels (for example, `01_opening.wav`, `02_chapter_name.wav`). Maintain a manifest or ordered input list so assembly cannot silently omit a chapter.

## Post-production tool

Run `python scripts/assemble_voiceover.py --help` for options. The script requires `ffmpeg` and `ffprobe`. It converts and verifies each chapter, inserts the requested gap, concatenates in the supplied order, performs two-pass loudness normalization, checks the final loudness/true peak, and optionally creates a ZIP of the normalized chapters. It does not generate speech or music.

## Resources

- Read `references/puck-profile.md` for the reusable voice and performance defaults.
- Use `scripts/assemble_voiceover.py` for repeatable post-processing.
