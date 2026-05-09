"""G2P entegrasyonlu feedback testi.

ğ ve â iceren kelimelerle TTS uret, alignment + feedback'i goster.
Beklenti: feedback artik 'bu ğ sessiz, "yapacağım" "yapacaım" olarak okunur'
gibi kelime-ozel notlar versin.
"""

import asyncio
from pathlib import Path

from align_and_score import assess
from feedback import make_feedback

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "data" / "validation_set" / "g2p_test"

PHRASES = [
    "yapacağım",
    "soğuk",
    "değil",
    "kâr",
    "hâlâ",
]


async def make_audio() -> None:
    import edge_tts
    OUT.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(PHRASES):
        path = OUT / f"{i:02d}.mp3"
        if path.with_suffix(".wav").exists():
            continue
        c = edge_tts.Communicate(p, "tr-TR-AhmetNeural")
        await c.save(str(path))
        # to wav 16k via ffmpeg
        import subprocess
        wav = path.with_suffix(".wav")
        subprocess.run(["ffmpeg", "-y", "-i", str(path), "-ar", "16000", "-ac", "1", str(wav)],
                       check=True, capture_output=True)
        path.unlink(missing_ok=True)


def main() -> None:
    asyncio.run(make_audio())
    for i, p in enumerate(PHRASES):
        wav = OUT / f"{i:02d}.wav"
        print(f"\n=== {p}  (audio: {wav.name}) ===")
        segs = assess(wav, p)
        # Bilerek 'kotu durum' simulasyonu: target metni biraz farkli ver
        # ki dusuk skor alip g2p'li notlarini gorelim.
        # Asil amac: yapilanan ses cikti dogru, biz 'merhaba' diye target verelim.
        bad_target = "merhaba" if i % 2 == 0 else p
        # Aslinda gercek target ile koyalim, dusuk skor olabilir cunku g sessiz vb.
        fb = make_feedback(segs, p)
        print(fb.feedback_text)


if __name__ == "__main__":
    main()
