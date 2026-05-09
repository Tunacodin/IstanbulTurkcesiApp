"""Uzun metinlerde pipeline'i stress-test et.
TTS ile metni sentezler, sonra dogru/yanlis target ile pipeline'i kosur."""

import asyncio
import json
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXERCISES = REPO_ROOT / "data" / "exercises" / "exercises.json"
OUT = REPO_ROOT / "data" / "validation_set" / "long_text"


async def synth_all() -> list[dict]:
    import edge_tts
    OUT.mkdir(parents=True, exist_ok=True)
    with open(EXERCISES, encoding="utf-8") as f:
        data = json.load(f)
    results = []
    for ex in data["exercises"]:
        if ex["type"] in ("kelime",):
            continue  # uzun metinlere odakla
        wav = OUT / f"{ex['id']}.wav"
        if not wav.exists():
            mp3 = wav.with_suffix(".mp3")
            c = edge_tts.Communicate(ex["text"], "tr-TR-AhmetNeural")
            await c.save(str(mp3))
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(mp3), "-ar", "16000", "-ac", "1", str(wav)],
                check=True, capture_output=True,
            )
            mp3.unlink(missing_ok=True)
        results.append({
            "id": ex["id"],
            "text": ex["text"],
            "type": ex["type"],
            "wav": wav,
        })
    return results


def main() -> None:
    items = asyncio.run(synth_all())
    from align_and_score import assess_with_transcription
    from feedback import make_feedback

    for item in items:
        wav = item["wav"]
        target = item["text"]
        print(f"\n=== {item['id']}  ({item['type']}, {len(target)} char) ===")
        print(f"  target: {target}")
        t0 = time.perf_counter()
        segs, trans = assess_with_transcription(wav, target)
        elapsed = time.perf_counter() - t0
        fb = make_feedback(segs, target, transcription=trans)
        # Audio suresini hesapla
        last_end = max((s.end_s for s in segs if s.char != "|"), default=0.0)
        print(f"  ses suresi (trim sonrasi): {last_end:.2f}s   pipeline: {elapsed:.2f}s")
        print(f"  transcription: '{trans}'")
        print(f"  match: {fb.transcription_match:.2f}  overall: {fb.overall_score:.2f}  verdict: {fb.verdict}")
        if fb.issues:
            print(f"  issues ({len(fb.issues)}):")
            for it in fb.issues[:6]:
                print(f"    • {it.kind:12s}  '{it.char}'  skor={it.score:.2f}")
            if len(fb.issues) > 6:
                print(f"    ... +{len(fb.issues)-6} daha")


if __name__ == "__main__":
    main()
