"""
prosody.py icin smoke test.
Ahmet wav'ı referans, Emel wav'ı 'kullanici' olarak kıyaslanır.
"""

from pathlib import Path

from align_and_score import assess
from prosody import extract_prosody, compare, report

REPO_ROOT = Path(__file__).resolve().parent.parent
TTS_DIR = REPO_ROOT / "data" / "validation_set" / "tts"

PHRASES = [
    ("00", "merhaba dunya"),
    ("03", "bu sabah erken kalktim"),
    ("06", "istanbul cok guzel bir sehir"),
]


def main() -> None:
    for idx, text in PHRASES:
        ref_wav = TTS_DIR / "ahmet" / f"{idx}.wav"
        user_wav = TTS_DIR / "emel" / f"{idx}.wav"
        print(f"\n=== '{text}' ===")
        ref_segs = assess(ref_wav, text)
        user_segs = assess(user_wav, text)
        ref_pros = extract_prosody(ref_wav, ref_segs)
        user_pros = extract_prosody(user_wav, user_segs)
        comp = compare(user_pros, ref_pros)
        print(report(comp))


if __name__ == "__main__":
    main()
