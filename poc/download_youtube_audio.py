"""4 diksiyon videosunun ses dosyalarini indir.

Cikti: data/knowledge/youtube_audio/<video_id>.wav (16kHz mono)

Kullanim:
    python download_youtube_audio.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TX_DIR = REPO_ROOT / "data" / "knowledge" / "youtube_transcripts"
AUDIO_DIR = REPO_ROOT / "data" / "knowledge" / "youtube_audio"


def download(video_id: str) -> Path | None:
    out_path = AUDIO_DIR / f"{video_id}.wav"
    if out_path.exists():
        print(f"  [{video_id}] zaten var, atlandı")
        return out_path
    out_template = str(AUDIO_DIR / f"{video_id}.%(ext)s")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-x",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--postprocessor-args", "-ar 16000 -ac 1",
        "-o", out_template,
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    print(f"  [{video_id}] indiriliyor...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        print(f"    HATA: {exc.stderr or exc}")
        return None
    if out_path.exists():
        size_mb = out_path.stat().st_size / 1024 / 1024
        print(f"    yazıldı: {out_path.name} ({size_mb:.1f} MB)")
        return out_path
    return None


def main() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    videos = []
    for path in TX_DIR.glob("*.json"):
        if path.name.startswith("_"):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        videos.append(data["video_id"])

    print(f"{len(videos)} video bulundu, ses dosyaları indiriliyor...")
    print(f"UYARI: Bu sadece içerik sahibi izinli/CC olan içerik için.\n")

    succeeded = 0
    for vid in videos:
        if download(vid):
            succeeded += 1
    print(f"\n{succeeded}/{len(videos)} ses indirildi → {AUDIO_DIR}")


if __name__ == "__main__":
    main()
