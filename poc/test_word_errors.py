"""Kullanicinin sundugu Anadolu agzı ornegini Edge TTS olmadan elle simule et.
Transcription'i bilerek 'guçuk vuş gağasıyla garıştırdı' tarzı yapip make_feedback'i kosur,
yeni word-level + critical-substitution mantigini dogrula."""

from align_and_score import CharSegment
from feedback import make_feedback


# Sahte segments (alignment kismi yuksek skor doner — sadece kelime hatasi mantigini test ediyoruz)
def fake_segments_for(text: str) -> list[CharSegment]:
    segs = []
    t = 0.0
    for i, c in enumerate(text):
        if c == " ":
            segs.append(CharSegment(char="|", start_s=t, end_s=t + 0.05, score=1.0, target_char="|"))
            t += 0.05
            continue
        segs.append(CharSegment(char=c.lower(), start_s=t, end_s=t + 0.08, score=0.95, target_char=c))
        t += 0.08
    return segs


CASES = [
    {
        "id": "anadolu_agiz",
        "target": "küçük bir kuş, açık pencereden odaya girdi. masanın üzerindeki kâğıtları gagasıyla karıştırdı, sonra hızla uçup gitti.",
        "transcription": "guçuk bir vuş açık pencereden odaya girdi masanın üzerindeki kağıtları gağasıyla garıştırdı sonra hızlı uçup gitti",
        "label": "Anadolu agzi: küçük→guçuk, kuş→vuş, gagasıyla→gağasıyla, karıştırdı→garıştırdı",
    },
    {
        "id": "tek_kelime_hata",
        "target": "merhaba dünya",
        "transcription": "merhaba dunya",
        "label": "Sadece â/u sapması (gerçek hata değil)",
    },
    {
        "id": "iki_kelime_hata",
        "target": "bugün hava çok güzel",
        "transcription": "bugün hava güzel",  # 'çok' düştü
        "label": "Bir kelime atlandi",
    },
    {
        "id": "kg_hatasi_tek",
        "target": "kar yağıyor",
        "transcription": "gar yağıyor",
        "label": "Tek kritik degisim (k→g)",
    },
]

for case in CASES:
    target = case["target"]
    trans = case["transcription"]
    print(f"\n=== {case['id']}  ({case['label']}) ===")
    print(f"  target:     '{target}'")
    print(f"  transcript: '{trans}'")
    segs = fake_segments_for(target)
    fb = make_feedback(segs, target, transcription=trans)
    print(f"  word_match: ?  overall: {fb.overall_score:.2f}  verdict: {fb.verdict}")
    print(f"  feedback_text:")
    for line in fb.feedback_text.splitlines():
        print(f"    {line}")
