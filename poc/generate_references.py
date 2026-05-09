"""Tum alistirmalar icin referans ses dosyasi uret.

Sonradan eğitmen kayıtlarıyla değiştirilecek; şimdilik Edge TTS
(tr-TR-AhmetNeural) kullanılır. Çıktı: data/exercises/refs/<id>.wav
ve metadata.json.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXERCISES_PATH = REPO_ROOT / "data" / "exercises" / "exercises.json"
OUT_DIR = REPO_ROOT / "data" / "exercises" / "refs"

DEFAULT_VOICE = "tr-TR-AhmetNeural"


async def synth_one(text: str, voice: str, mp3: Path) -> None:
    import edge_tts
    c = edge_tts.Communicate(text=text, voice=voice)
    await c.save(str(mp3))


def to_wav(mp3: Path, wav: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp3), "-ar", "16000", "-ac", "1", str(wav)],
        check=True, capture_output=True,
    )


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(EXERCISES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    meta = []
    for ex in data["exercises"]:
        wav = OUT_DIR / f"{ex['id']}.wav"
        if not wav.exists():
            mp3 = wav.with_suffix(".mp3")
            print(f"  [{ex['id']}] {ex['text'][:50]}")
            await synth_one(ex["text"], DEFAULT_VOICE, mp3)
            to_wav(mp3, wav)
            mp3.unlink(missing_ok=True)
        else:
            print(f"  [{ex['id']}] zaten var, atlandı")
        meta.append({
            "id": ex["id"],
            "text": ex["text"],
            "wav": str(wav.relative_to(REPO_ROOT)),
            "voice": DEFAULT_VOICE,
            "source": "tts-edge",
            "note": "Geçici referans — eğitmen stüdyo kayıtlarıyla değiştirilecek.",
        })
    with open(OUT_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"\n{len(meta)} referans kaydedildi → {OUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
