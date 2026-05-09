"""
POC pipeline'ını bir manifest üzerinde toplu çalıştırıp skor istatistikleri verir.

Manifest formatı (JSON):
    [
      {"audio_path": "data/.../cv_001.wav", "text": "merhaba dünya"},
      ...
    ]

Kullanım:
    python validate.py --manifest data/validation_set/cv_tr/manifest.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

# Windows konsolunda Turkce karakter icin UTF-8'e zorla
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent


def run(manifest_path: Path) -> None:
    from align_and_score import assess

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    overall_scores: list[float] = []
    failures = 0
    print(f"{'idx':>3}  {'avg':>5}  {'low':>4}  text")
    print("-" * 60)
    for i, item in enumerate(manifest):
        audio_path = REPO_ROOT / item["audio_path"]
        text = item["text"]
        try:
            segments = assess(audio_path, text)
        except Exception as exc:
            failures += 1
            print(f"{i:>3}  ERR    -    {text[:40]}  ({exc})")
            continue
        scores = [s.score for s in segments if s.char != "|"]
        if not scores:
            failures += 1
            print(f"{i:>3}  EMPTY  -    {text[:40]}")
            continue
        avg = statistics.fmean(scores)
        low = sum(1 for s in scores if s < 0.55)
        overall_scores.append(avg)
        print(f"{i:>3}  {avg:5.2f}  {low:>4}  {text[:40]}")

    print()
    if overall_scores:
        print(f"Örnek sayısı: {len(overall_scores)}  (başarısız: {failures})")
        print(f"Skor ortalaması : {statistics.fmean(overall_scores):.3f}")
        print(f"Skor medyanı    : {statistics.median(overall_scores):.3f}")
        print(f"Min - Max       : {min(overall_scores):.3f} - {max(overall_scores):.3f}")
        if statistics.fmean(overall_scores) < 0.5:
            print("\nUYARI: Skor ortalaması düşük. Pipeline'da sorun olabilir "
                  "(model, normalizasyon, eşik).")
        else:
            print("\nPipeline doğrulanmış görünüyor.")
    else:
        print("Hiç örnek başarıyla işlenemedi.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest)


if __name__ == "__main__":
    main()
