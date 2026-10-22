#!/usr/bin/env python3
"""Normalize and assemble chapter WAVs without generating or altering speech style."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE if capture else subprocess.PIPE,
    )


def ffmpeg_path() -> str:
    p = shutil.which("ffmpeg")
    if not p:
        raise RuntimeError("ffmpeg was not found on PATH")
    return p


def ffprobe_path() -> str:
    p = shutil.which("ffprobe")
    if not p:
        raise RuntimeError("ffprobe was not found on PATH")
    return p


def measure(path: Path, integrated: float, true_peak: float) -> dict[str, str]:
    cmd = [
        ffmpeg_path(), "-hide_banner", "-nostats", "-i", str(path),
        "-af", f"loudnorm=I={integrated}:TP={true_peak}:LRA=11:print_format=json",
        "-f", "null", "-",
    ]
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    blocks = re.findall(r"\{[\s\S]*?\}", p.stderr)
    if not blocks:
        raise RuntimeError(f"Could not parse loudnorm measurement for {path}\n{p.stderr[-1200:]}")
    return json.loads(blocks[-1])


def probe_summary(path: Path) -> dict[str, str]:
    cmd = [
        ffprobe_path(), "-v", "error", "-show_entries",
        "stream=sample_rate,channels,sample_fmt:format=duration",
        "-of", "json", str(path),
    ]
    data = json.loads(subprocess.check_output(cmd, text=True))
    stream = data["streams"][0]
    return {
        "sample_rate": stream.get("sample_rate", ""),
        "channels": str(stream.get("channels", "")),
        "sample_fmt": stream.get("sample_fmt", ""),
        "duration": data.get("format", {}).get("duration", ""),
    }


def concat_escape(value: Path) -> str:
    return str(value.resolve()).replace("\\", "\\\\").replace("'", "\\'")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize ordered chapter audio to mono WAV, insert gaps, assemble, and loudness-master."
    )
    parser.add_argument("--input-dir", type=Path, default=Path("."), help="Directory containing source chapter WAVs")
    parser.add_argument("--files", nargs="+", required=True, help="Chapter filenames in exact script order")
    parser.add_argument("--output", type=Path, required=True, help="Final full-length WAV path")
    parser.add_argument("--zip", dest="zip_path", type=Path, help="Optional ZIP path for normalized chapter WAVs")
    parser.add_argument("--gap", type=float, default=0.35, help="Silence between chapters in seconds (default: 0.35)")
    parser.add_argument("--sample-rate", type=int, default=48000, help="Output sample rate (default: 48000)")
    parser.add_argument("--integrated-lufs", type=float, default=-18.1, help="Integrated loudness target (default: -18.1 LUFS)")
    parser.add_argument("--true-peak", type=float, default=-1.5, help="Maximum true peak in dBTP (default: -1.5)")
    args = parser.parse_args()

    if args.gap < 0:
        parser.error("--gap must be zero or greater")
    chapters = [(args.input_dir / name).resolve() for name in args.files]
    missing = [str(p) for p in chapters if not p.is_file() or p.stat().st_size == 0]
    if missing:
        parser.error("Missing or empty chapter files:\n" + "\n".join(missing))

    ffmpeg_path()
    ffprobe_path()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.zip_path:
        args.zip_path.resolve().parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="voiceover_", dir=output.parent) as temp_name:
        temp = Path(temp_name)
        normalized: list[Path] = []
        for index, source in enumerate(chapters, start=1):
            target = temp / f"{index:02d}_{source.stem}.wav"
            run([
                ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
                "-ac", "1", "-ar", str(args.sample_rate), "-c:a", "pcm_s16le", str(target),
            ])
            normalized.append(target)

        concat_paths: list[Path] = []
        pause_path = temp / "chapter_gap.wav"
        if args.gap > 0 and len(normalized) > 1:
            run([
                ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", f"anullsrc=r={args.sample_rate}:cl=mono",
                "-t", f"{args.gap:.6f}", "-ac", "1", "-ar", str(args.sample_rate),
                "-c:a", "pcm_s16le", str(pause_path),
            ])
        for i, chapter in enumerate(normalized):
            concat_paths.append(chapter)
            if i < len(normalized) - 1 and args.gap > 0:
                concat_paths.append(pause_path)

        concat_list = temp / "concat.txt"
        concat_list.write_text(
            "\n".join(f"file '{concat_escape(p)}'" for p in concat_paths) + "\n",
            encoding="utf-8",
        )
        unmastered = temp / "assembled_unmastered.wav"
        run([
            ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-ac", "1", "-ar", str(args.sample_rate), "-c:a", "pcm_s16le", str(unmastered),
        ])

        first = measure(unmastered, args.integrated_lufs, args.true_peak - 0.2)
        linear = (
            f"loudnorm=I={args.integrated_lufs}:TP={args.true_peak - 0.2}:LRA=11:"
            f"measured_I={first['input_i']}:measured_TP={first['input_tp']}:"
            f"measured_LRA={first['input_lra']}:measured_thresh={first['input_thresh']}:"
            f"offset={first['target_offset']}:linear=true:print_format=summary"
        )
        run([
            ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(unmastered),
            "-af", linear, "-ac", "1", "-ar", str(args.sample_rate), "-c:a", "pcm_s16le", str(output),
        ])

        # If encoding/true-peak estimation leaves a slight overshoot, lower the
        # whole mix in tiny steps. This never changes speed or pitch.
        final_measure = measure(output, args.integrated_lufs, args.true_peak)
        tries = 0
        while float(final_measure["input_tp"]) > args.true_peak - 0.05 and tries < 4:
            reduction = float(final_measure["input_tp"]) - args.true_peak + 0.10
            adjusted = temp / "adjusted.wav"
            run([
                ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(output),
                "-af", f"volume=-{reduction:.3f}dB", "-ac", "1", "-ar", str(args.sample_rate),
                "-c:a", "pcm_s16le", str(adjusted),
            ])
            shutil.move(str(adjusted), str(output))
            final_measure = measure(output, args.integrated_lufs, args.true_peak)
            tries += 1

        if args.zip_path:
            zip_path = args.zip_path.resolve()
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
                for chapter in normalized:
                    archive.write(chapter, arcname=chapter.name)

    summary = probe_summary(output)
    print(f"Output: {output}")
    print(f"Duration: {float(summary['duration']):.2f} s")
    print(f"Format: {summary['sample_rate']} Hz, {summary['channels']} channel(s), {summary['sample_fmt']}")
    print(f"Integrated loudness measured: {final_measure['input_i']} LUFS")
    print(f"True peak measured: {final_measure['input_tp']} dBTP")
    if float(final_measure["input_tp"]) > args.true_peak:
        print("WARNING: true peak remains above target; consider a true-peak limiter or a slightly lower target.", file=sys.stderr)
    if args.zip_path:
        print(f"Chapter ZIP: {args.zip_path.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
