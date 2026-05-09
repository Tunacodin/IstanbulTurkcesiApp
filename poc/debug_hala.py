"""'hala' (kisa) ile 'hâlâ' (uzun) wav'larinin segment surelerini karsilastir."""

from pathlib import Path

from align_and_score import assess

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "data" / "validation_set" / "user_scenarios"

for sid, label in [("02_short_a", "TTS='hala'"), ("04_correct_long", "TTS='hâlâ'")]:
    wav = OUT / f"{sid}.wav"
    print(f"\n=== {sid}  ({label}, target='hâlâ') ===")
    segs = assess(wav, "hâlâ")
    for s in segs:
        if s.char == "|":
            continue
        print(f"  {s.char}  {s.start_s:5.3f} -> {s.end_s:5.3f}  duration={s.end_s-s.start_s:5.3f}s  score={s.score:.3f}")
    total_audio = max(s.end_s for s in segs if s.char != "|")
    durations = sorted(s.end_s - s.start_s for s in segs if s.char != "|")
    median = durations[len(durations) // 2]
    print(f"  total: {total_audio:.3f}s  median segment: {median:.3f}s")
