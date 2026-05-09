"""
Edge TTS ile Turkce test ornekleri uret.

Microsoft Edge'in Turkce neural seslerini (tr-TR-AhmetNeural, tr-TR-EmelNeural)
kullanir; ucretsiz, login gerektirmez. Pipeline dogrulamasi icin "altin"
referans sayilabilir cunku TTS bilinen dogru telaffuzu uretir.

Kullanim:
    python make_tts_samples.py
    # → data/validation_set/tts/{ahmet,emel}/*.wav + manifest.json
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "validation_set" / "tts"

VOICES = {
    "ahmet": "tr-TR-AhmetNeural",
    "emel": "tr-TR-EmelNeural",
}

PHRASES = [
    "merhaba dunya",
    "merhaba",
    "kar yagiyor",
    "bu sabah erken kalktim",
    "su kose yaz kosesi",
    "kirk kartal kalkmis",
    "istanbul cok guzel bir sehir",
    "haberler",
]


async def synthesize_one(text: str, voice: str, mp3_path: Path) -> None:
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(mp3_path))


def to_wav_16k(mp3_path: Path, wav_path: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-i", str(mp3_path),
        "-ar", "16000", "-ac", "1",
        str(wav_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for voice_key, voice_id in VOICES.items():
        sub = OUT_DIR / voice_key
        sub.mkdir(exist_ok=True)
        for i, phrase in enumerate(PHRASES):
            mp3 = sub / f"{i:02d}.mp3"
            wav = sub / f"{i:02d}.wav"
            print(f"  [{voice_key}] {phrase}")
            await synthesize_one(phrase, voice_id, mp3)
            to_wav_16k(mp3, wav)
            mp3.unlink(missing_ok=True)
            manifest.append({
                "audio_path": str(wav.relative_to(REPO_ROOT)),
                "text": phrase,
                "voice": voice_id,
            })
    manifest_path = OUT_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n{len(manifest)} ornek yazildi  ->  {OUT_DIR}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    asyncio.run(main())
