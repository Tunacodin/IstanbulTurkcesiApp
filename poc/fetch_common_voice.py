"""
Mozilla Common Voice TR'den birkaç doğrulanmış örnek çek.

Kullanım:
    # Önce HuggingFace'e login: huggingface-cli login
    # ve Mozilla Common Voice şartlarını HF'de kabul et.

    python fetch_common_voice.py --count 10 --split validation

Çıktı:
    data/validation_set/cv_tr/<id>.wav
    data/validation_set/cv_tr/manifest.json

Notlar:
- "validation" split'i toplulukça onaylanmış (3+ olumlu oy) örnekleri içerir.
  Pipeline doğrulaması için en uygunu.
- Streaming modu kullanılıyor; tüm dataset (~6 GB TR) inmiyor.
- Common Voice TR ses kalitesi karışık (telefon, dizüstü mic, vs).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "validation_set" / "cv_tr"
TARGET_SR = 16_000


def fetch(count: int, split: str) -> list[dict]:
    from datasets import load_dataset
    print(f"Common Voice TR / {split} streaming başlatılıyor...")
    ds = load_dataset(
        "mozilla-foundation/common_voice_17_0",
        "tr",
        split=split,
        streaming=True,
    )
    samples = []
    for sample in ds:
        if len(samples) >= count:
            break
        if not sample["sentence"].strip():
            continue
        samples.append(sample)
    return samples


def save(samples: list[dict]) -> list[dict]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i, s in enumerate(samples):
        audio = s["audio"]
        arr = np.asarray(audio["array"], dtype=np.float32)
        sr = audio["sampling_rate"]
        if sr != TARGET_SR:
            import librosa
            arr = librosa.resample(arr, orig_sr=sr, target_sr=TARGET_SR)
        out_path = OUT_DIR / f"cv_{i:03d}.wav"
        sf.write(out_path, arr, TARGET_SR)
        manifest.append({
            "audio_path": str(out_path.relative_to(REPO_ROOT)),
            "text": s["sentence"],
            "client_id": s.get("client_id", ""),
            "duration_s": float(len(arr) / TARGET_SR),
        })
        print(f"  [{i:3d}] {len(arr)/TARGET_SR:5.2f}s  {s['sentence'][:60]}")
    manifest_path = OUT_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n{len(manifest)} örnek yazıldı → {OUT_DIR}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--split", default="validation",
                        choices=["validation", "test", "train"])
    args = parser.parse_args()
    samples = fetch(args.count, args.split)
    save(samples)


if __name__ == "__main__":
    main()
