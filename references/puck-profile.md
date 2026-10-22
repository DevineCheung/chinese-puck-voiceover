# Puck Mandarin Explainer Profile

## Voice identity and limits

- Voice name: `Puck`.
- Language code: `zh-CN`.
- Intended delivery: Mandarin Chinese, youthful male-presenting, warm, clear, curious; friendly explainer rather than childish character, newsreader, or advertisement.
- The voice name is not the underlying model name. `generate_speech` does not expose the backend model/version or random seed. Reusing the same voice and instructions can improve consistency but cannot guarantee identical output across sessions.

## Performance defaults

Aim for approximately 280–310 Chinese characters per minute when suitable for the script. Let examples and simple lists move slightly faster; slow down for concepts, central claims, legal or rights boundaries, and important conclusions. Make questions sound genuinely curious. Keep risk passages measured. End with warmth and quiet confidence rather than a dramatic fall or prolonged tail.

Use approximate pause intentions only as a guide: short pauses 0.2–0.4 seconds, section-level pauses 0.6–0.9 seconds, and important questions about 1 second. The synthesis pause tags are expressive cues, not a guarantee of exact timing. Enforce precise gaps between chapter files during post-processing.

Recommended concise style baseline for synthesis: `warm, clear, curious, moderately brisk`. For a specific section, choose a short variant such as `warm, measured, precise` or `warm, thoughtful, restrained`, while preserving the same Puck voice. Keep directions in English and roughly 1–6 words. Do not put age, gender, accent, language, or long persona descriptions in `style`; select voice and language in their dedicated fields.

## Text conventions

- Do not read the title, section headings, square-bracket stage directions, or parenthetical pronunciation notes when the user marks them as non-spoken.
- Read an opening question when the user explicitly marks it as spoken.
- Keep a spoken brand outro as a separate chapter file when requested.
- Spell out an ambiguous number or pronunciation only when needed to ensure the intended reading; do not silently rewrite the user's factual text.

## Standard delivery defaults

- Individual chapters: WAV, mono, 48 kHz, 16-bit PCM.
- Full mix: chapter order preserved, 0.35 seconds of silence between chapters, no background music unless requested.
- Loudness target: approximately -18.1 LUFS integrated, true peak no higher than -1.5 dBTP. Verify the rendered file; practical encoders and true-peak estimation can cause small deviations, so allow a small safety margin.
- Do not change playback speed, pitch, or add reverb unless explicitly requested.
- Deliver a full WAV plus a ZIP containing normalized chapter WAVs. Report measured format and duration rather than implying exact loudness if the meter differs slightly from target.
