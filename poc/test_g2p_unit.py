"""G2P-aware feedback unit test — bilerek dusuk skorlar."""

from align_and_score import CharSegment
from feedback import make_feedback

CASES = [
    ("değil",      "ğ", 0.10),
    ("yapacağım",  "ğ", 0.05),
    ("kâr",        "â", 0.20),
    ("soğuk",      "o", 0.15),
    ("hâlâ",       "â", 0.10),
]

for target, bad_char, bad_score in CASES:
    segs = []
    for i, c in enumerate(target):
        score = bad_score if c == bad_char else 0.95
        segs.append(CharSegment(char=c, start_s=i*0.1, end_s=(i+1)*0.1, score=score))
    fb = make_feedback(segs, target)
    print(f"=== {target}  (bilerek bozuk: '{bad_char}' = {bad_score}) ===")
    print(fb.feedback_text)
    print()
