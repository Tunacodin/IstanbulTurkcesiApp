"""Lexicon-tabanli hata desen tespitini make_feedback uzerinde test et."""
from align_and_score import CharSegment
from feedback import make_feedback


def fake_segments_for(text: str) -> list[CharSegment]:
    segs = []
    t = 0.0
    for c in text:
        if c == " ":
            segs.append(CharSegment(char="|", start_s=t, end_s=t + 0.05, score=1.0, target_char="|"))
            t += 0.05
            continue
        segs.append(CharSegment(char=c.lower(), start_s=t, end_s=t + 0.08, score=0.95, target_char=c))
        t += 0.08
    return segs


CASES = [
    ("R yutulması", "ne yapıyorsun", "ne yapıyosun"),
    ("R yutulması (cümle)", "geliyor musun", "geliyo musun"),
    ("H yutulması (kelime)", "merhaba dünya", "meraba dunya"),
    ("H yutulması (çoklu)", "kahve içtim ahmet", "ka:ve içtim a:met"),
    ("Kritik ünsüz (önceden çalışan)", "küçük kuş", "guçuk vuş"),
    ("Karma: H + kritik", "merhaba ahmet", "meraba amet"),
    ("Doğru söyleyen", "merhaba dünya", "merhaba dünya"),
]

for label, target, spoken in CASES:
    print(f"\n=== {label} ===")
    print(f"  target:  '{target}'")
    print(f"  spoken:  '{spoken}'")
    segs = fake_segments_for(target)
    fb = make_feedback(segs, target, transcription=spoken)
    print(f"  overall: {fb.overall_score:.2f}  verdict: {fb.verdict}")
    for it in fb.issues:
        if it.kind == "kelime" or it.kind in ("r_yutulmasi", "h_yutulmasi", "kritik_unsuz"):
            print(f"    [{it.kind}]  '{it.target_word}' -> '{it.spoken_word}'")
            print(f"       {it.advice}")
