"""Vurgu yeri ölçümünü TTS örnekleri üzerinde test et."""

from pathlib import Path
from align_and_score import assess
from prosody import measure_word_stress

REPO_ROOT = Path(__file__).resolve().parent.parent

CASES = [
    (REPO_ROOT / "data" / "validation_set" / "tts" / "ahmet" / "06.wav",
     "istanbul cok guzel bir sehir"),
    (REPO_ROOT / "data" / "exercises" / "refs" / "cumle-001.wav",
     "yarın sabah erken kalkacağım"),
    (REPO_ROOT / "data" / "exercises" / "refs" / "cumle-002.wav",
     "bugün hava çok güzel, parka gitmeyi düşünüyorum"),
]

for wav, target in CASES:
    if not wav.exists():
        print(f"SKIP {wav.name}")
        continue
    print(f"\n=== {wav.name}  '{target}' ===")
    segments = assess(wav, target)
    measurements = measure_word_stress(wav, segments, target)
    for sm in measurements:
        marked_expected = "-".join(
            f"[{s}]" if i == sm.expected_stress_idx else s
            for i, s in enumerate(sm.syllables)
        )
        marked_measured = "-".join(
            f"({s})" if i == sm.measured_stress_idx else s
            for i, s in enumerate(sm.syllables)
        )
        status = "✓" if sm.stress_correct else "✗" if sm.confident else "?"
        print(f"  {status} {sm.word:18s}  beklenen: {marked_expected:30s}  ölçülen: {marked_measured}")
        if not sm.stress_correct and sm.confident:
            print(f"      F0: {sm.syllable_f0}  Energy: {sm.syllable_energy}")
