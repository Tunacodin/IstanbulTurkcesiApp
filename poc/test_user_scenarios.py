"""Kullanicinin bildirdigi iki senaryoyu Edge TTS ile simule et:
1. TTS 'kalkicam' soyler, target 'kalkacagim' -> mismatch yakalanmali
2. TTS 'hala' (kisa a) soyler, target 'hala' (uzun a) -> uzun-unlu hatasi
"""

import asyncio
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "data" / "validation_set" / "user_scenarios"

CASES = [
    # (TTS yazdiklari, target_text, scenario_id)
    ("kalkıcam",         "kalkacağım", "01_colloquial"),
    ("hala",             "hâlâ",       "02_short_a"),
    # Pozitif kontroller
    ("kalkacağım",       "kalkacağım", "03_correct_full"),
    ("hâlâ",             "hâlâ",       "04_correct_long"),
]


async def synth() -> None:
    import edge_tts
    OUT.mkdir(parents=True, exist_ok=True)
    for tts_text, _, sid in CASES:
        wav = OUT / f"{sid}.wav"
        if wav.exists():
            continue
        mp3 = wav.with_suffix(".mp3")
        c = edge_tts.Communicate(tts_text, "tr-TR-AhmetNeural")
        await c.save(str(mp3))
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3), "-ar", "16000", "-ac", "1", str(wav)],
            check=True, capture_output=True,
        )
        mp3.unlink(missing_ok=True)


def main() -> None:
    asyncio.run(synth())
    from align_and_score import assess_with_transcription
    from feedback import make_feedback

    for tts_text, target, sid in CASES:
        wav = OUT / f"{sid}.wav"
        print(f"\n=== {sid}:  TTS='{tts_text}'  target='{target}' ===")
        segs, trans = assess_with_transcription(wav, target)
        fb = make_feedback(segs, target, transcription=trans)
        print(f"  transcription: '{trans}'")
        print(f"  match: {fb.transcription_match:.2f}  alignment_avg: "
              f"{sum(s.score for s in segs if s.char != '|')/max(1,len([s for s in segs if s.char != '|'])):.2f}")
        print(f"  overall: {fb.overall_score:.2f}  verdict: {fb.verdict}")
        print("  feedback:")
        for line in fb.feedback_text.splitlines():
            print(f"    {line}")


if __name__ == "__main__":
    main()
