"""YT diksiyon transkriptlerinden 'X değil Y' / 'X yerine Y' / 'X şeklinde'
kalıplarını arayıp aday lexicon kayıtları çıkar.

Heuristic regex ile: bu LLM kalitesinde değil ama bedava ve hızlı.
Çıktı: data/lexicon/transcript_candidates.json (manuel review için)
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TX_DIR = REPO_ROOT / "data" / "knowledge" / "youtube_transcripts"
OUT = REPO_ROOT / "data" / "lexicon" / "transcript_candidates.json"

# Türkçe kelime: harf + çğşıöü
WORD_RE = r"[A-Za-zçğışöüâîûÇĞIŞİÖÜÂÎÛ]+(?:'[a-zçğışöüâîû]+)?"

# Kalıplar — her grup iki kelime: target ve spoken (ya da tersi).
PATTERNS = [
    # "X değil Y"  → X yanlış, Y doğru (genelde)
    (re.compile(rf"({WORD_RE})\s+değil\s+({WORD_RE})", re.IGNORECASE),
     "X_degil_Y", "X yanlış, Y doğru"),
    # "X yerine Y"
    (re.compile(rf"({WORD_RE})\s+yerine\s+({WORD_RE})", re.IGNORECASE),
     "X_yerine_Y", "X yanlış, Y doğru"),
    # "X şeklinde okunur" / "X olarak okunur"
    (re.compile(rf"({WORD_RE})\s+(?:şeklinde|olarak)\s+okun", re.IGNORECASE),
     "X_okunur", "X telaffuz biçimi"),
    # "X gibi söyleniyor" / "X gibi söyleyenler"
    (re.compile(rf"({WORD_RE})\s+gibi\s+söyl", re.IGNORECASE),
     "X_gibi", "X yaygın yanlış telaffuz"),
    # "doğrusu X" / "doğrusu X'tir"
    (re.compile(rf"doğrusu\s+({WORD_RE})", re.IGNORECASE),
     "dogrusu_X", "X doğru biçim"),
    # "X olmalı"
    (re.compile(rf"({WORD_RE})\s+olmalı", re.IGNORECASE),
     "X_olmali", "X olması gereken"),
]


def main() -> None:
    candidates: dict[str, list[dict]] = defaultdict(list)
    per_video_count: dict[str, int] = {}

    for path in TX_DIR.glob("*.json"):
        if path.name.startswith("_"):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        full_text = data.get("transcript_text", "")
        title = data.get("title", "")
        vid = data.get("video_id", "")
        n_found = 0

        for pat, kind, note in PATTERNS:
            for m in pat.finditer(full_text):
                # Bağlam: matchin etrafından ±60 karakter
                start = max(0, m.start() - 60)
                end = min(len(full_text), m.end() + 60)
                context = full_text[start:end].replace("\n", " ").strip()
                groups = m.groups()
                candidates[kind].append({
                    "video_id": vid,
                    "title": title,
                    "match": m.group(0),
                    "groups": list(groups),
                    "context": "..." + context + "...",
                })
                n_found += 1
        per_video_count[f"{vid} | {title[:50]}"] = n_found

    print("Bulunan adaylar (kalıba göre):")
    for kind, items in candidates.items():
        print(f"  {kind:20s}  {len(items)} aday")
    print("\nVideo başına aday sayısı:")
    for k, v in per_video_count.items():
        print(f"  {v:3d}  {k}")

    out_data = {
        "_meta": {
            "kaynak": "4 YT diksiyon transkripti, regex pattern matching",
            "kullanim": "Manuel review sonrası g2p_pairs.json veya error_patterns.json'a aktarılır.",
            "uyari": "Heuristic; her aday gerçek bir kural değil — bağlam okunmalı.",
        },
        "candidates_by_pattern": {k: v for k, v in candidates.items()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"\nKaydedildi: {OUT}")


if __name__ == "__main__":
    main()
