"""İki senaryoyu test eder:
  1. 'merhaba' ses + 'yağmur' target -> transcription mismatch yakalanmalı
  2. 'hala' ses (kısa a) + 'hâlâ' target -> uzun ünlü süre kontrolü
"""

from pathlib import Path

from align_and_score import assess_with_transcription
from feedback import make_feedback

REPO_ROOT = Path(__file__).resolve().parent.parent
TTS = REPO_ROOT / "data" / "validation_set" / "tts"

CASES = [
    # 'merhaba' wav + 'yagmur' target → mismatch beklenmeli
    (TTS / "ahmet" / "01.wav", "merhaba", "Dogru durum (kontrol)"),
    (TTS / "ahmet" / "01.wav", "yağmur", "Mismatch durumu — eskiden 0.17, mismatch cezasiyla daha düşmeli"),
    # 'hâlâ' aslinda TTS dogru söyledi, biraz uzun ünlüyle. Hala = kısa a, ama TTS â yapamadıysa hata cıkar
    (TTS / "ahmet" / "00.wav", "hâlâ", "Wav 'merhaba dunya' diyor; 'hâlâ' target ile karışık"),
]

for wav, target, desc in CASES:
    print(f"\n=== {desc} ===")
    print(f"  audio: {wav.name},  target: '{target}'")
    segs, trans = assess_with_transcription(wav, target)
    fb = make_feedback(segs, target, transcription=trans)
    print(f"  transcription: '{trans}'")
    print(f"  match ratio: {fb.transcription_match:.2f}")
    print(f"  overall_score: {fb.overall_score:.2f}  verdict: {fb.verdict}")
    print(f"  feedback:\n{fb.feedback_text}")
