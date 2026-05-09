"""Tam pipeline + prosody entegrasyon testi."""

from pathlib import Path

from align_and_score import assess
from prosody import extract_prosody, compare
from feedback import make_feedback

REPO_ROOT = Path(__file__).resolve().parent.parent
TTS = REPO_ROOT / "data" / "validation_set" / "tts"

CASES = [
    ("merhaba dunya", "00"),
    ("istanbul cok guzel bir sehir", "06"),
]

for text, idx in CASES:
    user = TTS / "ahmet" / f"{idx}.wav"
    ref = TTS / "emel" / f"{idx}.wav"
    print(f"\n========== '{text}' ==========")
    user_segs = assess(user, text)
    ref_segs = assess(ref, text)
    user_pros = extract_prosody(user, user_segs)
    ref_pros = extract_prosody(ref, ref_segs)
    comp = compare(user_pros, ref_pros)
    fb = make_feedback(user_segs, text, prosody=comp)
    print(fb.feedback_text)
    print(f"\nGenel skor: {fb.overall_score:.3f}  |  Verdict: {fb.verdict}")
    print(f"Vurgu sapmasi: {comp.overall_severity:.2f}")
