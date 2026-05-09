"""Naturalness tespitini gercek kayitlar uzerinde test et.
Edge TTS ile uretilmis temiz 'merhaba' wav'i ile, sonra fake bir 'tutuk'
duruma karsi kontrol."""

from pathlib import Path

from align_and_score import assess_with_transcription
from feedback import make_feedback
from prosody import analyze_naturalness

REPO_ROOT = Path(__file__).resolve().parent.parent
TTS = REPO_ROOT / "data" / "validation_set" / "tts"

CASES = [
    (TTS / "ahmet" / "01.wav", "merhaba", "Edge TTS — temiz 'merhaba'"),
    (TTS / "ahmet" / "02.wav", "kar yagiyor", "Kısa cümle"),
    (TTS / "ahmet" / "03.wav", "bu sabah erken kalktim", "Orta uzunluk"),
    (TTS / "ahmet" / "06.wav", "istanbul cok guzel bir sehir", "Uzun cümle"),
]

for wav, target, desc in CASES:
    if not wav.exists():
        continue
    print(f"\n=== {desc} ===")
    print(f"  audio: {wav.name}, target: '{target}'")
    segs, trans = assess_with_transcription(wav, target)
    nat = analyze_naturalness(wav, segs, target)
    print(f"  speech_rate: {nat.speech_rate_cps} cps")
    print(f"  F0 range:    {nat.f0_range_semitones} semitone")
    print(f"  HNR:         {nat.hnr_db} dB  (>12 sağlıklı)")
    print(f"  Intensity:   {nat.intensity_range_db} dB dinamik aralık")
    print(f"  monotonik: {nat.is_monotonic}, yavaş: {nat.is_too_slow}, "
          f"hızlı: {nat.is_too_fast}, choppy: {nat.is_choppy}, "
          f"hırıltı: {nat.is_breathy_or_noisy}, düz_genlik: {nat.has_flat_intensity}")
    if nat.intra_word_pauses_s:
        print(f"  pauses: {nat.intra_word_pauses_s}")
    if nat.issues:
        print(f"  ISSUES:")
        for it in nat.issues:
            print(f"    • {it}")
    fb = make_feedback(segs, target, transcription=trans, naturalness=nat)
    print(f"  overall: {fb.overall_score:.2f}  verdict: {fb.verdict}")
