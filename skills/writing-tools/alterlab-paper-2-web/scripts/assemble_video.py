#!/usr/bin/env python3
"""assemble_video.py - turn slide images + a narration script into an MP4 (keyless).

Claude writes the narration (one entry per slide) from the paper; this script voices it with a
LOCAL text-to-speech model (Piper; no account, no API key), or uses the author's own
recordings, writes SubRip captions, and assembles the video with ffmpeg.

    # narration.json: [{"slide": "slides/slide-001.png", "text": "In this talk ..."}, ...]
    uv run --python ">=3.11" --with piper-tts python scripts/assemble_video.py narration.json \\
        -o video/paper_video.mp4 --voice voices/en_US-lessac-medium.onnx
    # author-recorded audio instead (audio/01.wav, audio/02.mp3, ... in slide order)
    python scripts/assemble_video.py narration.json -o video/paper_video.mp4 --audio-dir audio/
    # captions only, timed at --wpm words per minute (silent video)
    python scripts/assemble_video.py narration.json -o video/paper_video.mp4 --silent

A Piper voice is two files (<name>.onnx + <name>.onnx.json), fetched once from Hugging Face
with `uv run --with piper-tts python -m piper.download_voices en_US-lessac-medium`. Outputs:
the MP4 (H.264 + AAC, 1920 px wide, captions as a selectable subtitle track), a sidecar .srt,
and per-slide timings in <output>.json. Needs ffmpeg and ffprobe on PATH.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or proc.stdout).strip().splitlines()[-8:])
        raise RuntimeError(f"{cmd[0]} failed (exit {proc.returncode}):\n{tail}")


def _duration(path: Path) -> float:
    if path.suffix.lower() == ".wav":
        with wave.open(str(path)) as wf:
            return wf.getnframes() / float(wf.getframerate())
    proc = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                           "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(proc.stdout.strip())


def _ts(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _chunks(text: str, words: int = 12) -> list[str]:
    sentences = re.split(r"(?<=[.!?;:])\s+", text.strip())
    out: list[str] = []
    for sent in sentences:
        toks = sent.split()
        for i in range(0, len(toks), words):
            out.append(" ".join(toks[i:i + words]))
    return [c for c in out if c]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path, help="narration JSON: [{slide, text}, ...]")
    ap.add_argument("-o", "--output", type=Path, required=True, help="output .mp4")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--voice", type=Path, help="Piper voice model (.onnx) for local TTS")
    src.add_argument("--audio-dir", type=Path, help="author recordings, one file per slide, sorted")
    src.add_argument("--silent", action="store_true", help="no audio; captions timed by --wpm")
    ap.add_argument("--wpm", type=float, default=150, help="speaking rate for --silent timing")
    ap.add_argument("--pause", type=float, default=0.6, help="seconds of hold after each slide")
    ap.add_argument("--width", type=int, default=1920)
    args = ap.parse_args(argv)

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            print(f"error: {tool} not found on PATH (install FFmpeg)", file=sys.stderr)
            return 2
    try:
        items = json.loads(args.script.read_text(encoding="utf-8"))
        base = args.script.parent
        slides = [(base / it["slide"]).resolve() for it in items]
        texts = [str(it.get("text", "")).strip() for it in items]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"error: cannot read the narration script: {exc}", file=sys.stderr)
        return 2
    missing = [str(s) for s in slides if not s.is_file()]
    if missing:
        print(f"error: slide image(s) not found: {missing[:3]}", file=sys.stderr)
        return 2

    recordings: list[Path] = []
    if args.audio_dir:
        recordings = sorted(p for p in args.audio_dir.iterdir()
                            if p.suffix.lower() in (".wav", ".mp3", ".m4a", ".flac", ".ogg"))
        if len(recordings) != len(items):
            print(f"error: {len(recordings)} recordings for {len(items)} slides", file=sys.stderr)
            return 2
    voice = None
    if args.voice:
        try:
            from piper import PiperVoice
        except ImportError:
            print("error: --voice needs piper-tts (`uv run --with piper-tts ...`)", file=sys.stderr)
            return 2
        voice = PiperVoice.load(str(args.voice))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    timings, srt, t0 = [], [], 0.0
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        clips = []
        for i, (slide, text) in enumerate(zip(slides, texts), 1):
            audio = None
            if voice is not None:
                audio = tmp / f"{i:03d}.wav"
                with wave.open(str(audio), "wb") as wf:
                    voice.synthesize_wav(text, wf)
            elif recordings:
                audio = recordings[i - 1]
            speech = _duration(audio) if audio else max(2.0, len(text.split()) / args.wpm * 60)
            dur = speech + args.pause
            clip = tmp / f"{i:03d}.mp4"
            scale = f"scale={args.width}:-2:flags=lanczos,format=yuv420p"
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "25",
                   "-t", f"{dur:.3f}", "-i", str(slide)]
            if audio:
                cmd += ["-i", str(audio), "-af", f"apad=pad_dur={args.pause}"]
            else:
                cmd += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=44100:cl=mono"]
            cmd += ["-vf", scale, "-c:v", "libx264", "-tune", "stillimage", "-r", "25",
                    "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "1",
                    "-t", f"{dur:.3f}", str(clip)]
            _run(cmd)
            clips.append(clip)
            chunks = _chunks(text) or [""]
            total_words = sum(len(c.split()) for c in chunks) or 1
            cursor = t0
            for c in chunks:
                span = speech * len(c.split()) / total_words
                if c:
                    srt.append((cursor, cursor + span, c))
                cursor += span
            timings.append({"slide": str(slide), "start": round(t0, 2), "duration": round(dur, 2)})
            t0 += dur
        listing = tmp / "clips.txt"
        listing.write_text("".join(f"file '{c}'\n" for c in clips), encoding="utf-8")
        srt_path = args.output.with_suffix(".srt")
        srt_path.write_text("".join(f"{n}\n{_ts(a)} --> {_ts(b)}\n{line}\n\n"
                                    for n, (a, b, line) in enumerate(srt, 1)), encoding="utf-8")
        _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
              "-i", str(srt_path), "-map", "0:v", "-map", "0:a", "-map", "1:s", "-c:v", "copy",
              "-c:a", "copy", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
              str(args.output)])
    report = {"output": str(args.output), "captions": str(srt_path), "slides": len(items),
              "duration_s": round(t0, 1), "narration": "piper (local)" if voice else
              ("author recordings" if recordings else "none (captions only)"),
              "timings": timings}
    args.output.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "timings"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
