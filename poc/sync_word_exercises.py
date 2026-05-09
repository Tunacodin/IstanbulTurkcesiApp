"""Telaffuzu olmayan kelime alistirmalarini sil + Mennan Sahin word_clips
indeksinden yeni kelime alistirmalari ekle.

Adimlar:
  1. word_clips_index.json yukle (1498 kelime)
  2. exercises.json'daki "kelime" tipindeki alistirmalardan, indekste olmayanlari sil
  3. Indeksteki en kaliteli kelimelerden yeni alistirma ekle (kelime-yt-*)
  4. Hepsi ref_source=word_clip kullansin (Mennan Sahin sesi)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EX_PATH = REPO_ROOT / "data" / "exercises" / "exercises.json"
INDEX_PATH = REPO_ROOT / "data" / "knowledge" / "word_clips_index.json"
LEX_G2P = REPO_ROOT / "data" / "lexicon" / "g2p_pairs.json"


def normalize_lookup(w: str) -> str:
    w = w.replace("I", "ı").replace("İ", "i").lower()
    return re.sub(r"[^\wçğışöü]", "", w)


def load_lexicon_words() -> set[str]:
    out: set[str] = set()
    if not LEX_G2P.exists():
        return out
    with open(LEX_G2P, encoding="utf-8") as f:
        data = json.load(f)
    for key, group in data.items():
        if isinstance(group, dict) and not key.startswith("_meta"):
            for k in group:
                if not k.startswith("_"):
                    out.add(k.lower())
    return out


def is_useful(word: str, occs: list[dict], lex_words: set[str]) -> tuple[bool, list[str]]:
    """Bu kelime alistirma olmaya deger mi?"""
    reasons = []
    w_low = word.lower()
    best_score = max((o.get("score", 0) for o in occs), default=0)
    best_dur = max((o.get("duration_s", 0) for o in occs), default=0)

    # Kalite filtresi
    if best_score < 0.55 or best_dur < 0.18:
        return False, []
    if len(w_low) <= 3:
        return False, []

    if w_low in lex_words:
        reasons.append("sözlük")
    if any(c in word for c in "âîû"):
        reasons.append("uzun-ünlü")
    if "ğ" in w_low:
        reasons.append("ğ-silme")
    if w_low.endswith(("yor", "yorsun", "yorlar", "yorum", "yoruz")):
        reasons.append("R-yutulması-adayı")
    if "h" in w_low and len(w_low) >= 4 and not w_low.startswith("h"):
        reasons.append("H-yutulması-adayı")
    if not reasons and best_score >= 0.85:
        reasons.append("temiz-örnek")

    return (len(reasons) > 0), reasons


def make_focus(reasons: list[str]) -> str:
    if "uzun-ünlü" in reasons:
        return "uzun ünlü"
    if "ğ-silme" in reasons:
        return "ğ silinir, ünlü uzar"
    if "R-yutulması-adayı" in reasons:
        return "-yor ekinde R'nin korunması"
    if "H-yutulması-adayı" in reasons:
        return "h sesinin yutulmaması"
    return "telaffuz pratiği"


def difficulty_for(word: str, reasons: list[str]) -> int:
    s = 1
    if "uzun-ünlü" in reasons: s += 1
    if "ğ-silme" in reasons: s += 1
    if len(word) > 7: s += 1
    if len(word) > 12: s += 1
    return min(5, s)


def main() -> None:
    if not INDEX_PATH.exists():
        print(f"Indeks yok: {INDEX_PATH}")
        return
    with open(INDEX_PATH, encoding="utf-8") as f:
        index = json.load(f)
    with open(EX_PATH, encoding="utf-8") as f:
        ex_data = json.load(f)

    print(f"word_clips_index: {len(index)} kelime")
    print(f"exercises.json toplam: {len(ex_data['exercises'])} alıştırma")

    # 1) Telaffuzu olmayan kelime tipi alıştırmaları SİL
    keep = []
    removed = []
    for ex in ex_data["exercises"]:
        if ex.get("type") != "kelime":
            keep.append(ex)
            continue
        # Tek kelime ise indekste var mı bak
        word_text = ex.get("text", "").strip()
        key = normalize_lookup(word_text)
        if key and key in index:
            keep.append(ex)
        else:
            # Telaffuzu yok, sil
            removed.append(ex.get("id", "?") + " (" + word_text + ")")
    print(f"\nTelaffuzu olmayan {len(removed)} kelime alıştırması silindi:")
    for r in removed[:10]:
        print(f"  - {r}")
    if len(removed) > 10:
        print(f"  ... +{len(removed)-10} daha")

    # 2) Yeni Mennan Şahin kelime alıştırmaları üret
    lex_words = load_lexicon_words()
    candidates: list[tuple[str, list[dict], list[str]]] = []
    for key, occs in index.items():
        ok, reasons = is_useful(key, occs, lex_words)
        if ok:
            candidates.append((key, occs, reasons))

    candidates.sort(key=lambda c: (-len(c[2]), -max(o.get("score", 0) for o in c[1])))
    selected = candidates[:80]
    print(f"\nIndeksten seçilen {len(selected)} yeni kelime (skor + sebep sırasıyla):")
    for w, occs, rs in selected[:15]:
        best = max(occs, key=lambda o: o.get("score", 0))
        print(f"  {w:18s} ({', '.join(rs):28s}) skor={best['score']}")

    # Mevcut text'leri ve ID counter
    existing_texts = {normalize_lookup(ex["text"]) for ex in keep}
    next_idx = 1
    for ex in keep:
        m = re.match(r"kelime-yt-(\d+)$", ex.get("id", ""))
        if m:
            next_idx = max(next_idx, int(m.group(1)) + 1)

    new_exercises = []
    for word, occs, reasons in selected:
        if word in existing_texts:
            continue
        ex_id = f"kelime-yt-{next_idx:03d}"
        next_idx += 1
        new_exercises.append({
            "id": ex_id,
            "type": "kelime",
            "text": word,
            "focus": make_focus(reasons),
            "difficulty": difficulty_for(word, reasons),
            "notes": f"Mennan Şahin video kütüphanesinden ({len(occs)} örnek). Kategori: {', '.join(reasons)}",
            "ref_source": "word_clip",
        })

    print(f"\n{len(new_exercises)} yeni kelime alıştırması ekleniyor")

    ex_data["exercises"] = keep + new_exercises
    with open(EX_PATH, "w", encoding="utf-8") as f:
        json.dump(ex_data, f, ensure_ascii=False, indent=2)
    print(f"\nYeni toplam: {len(ex_data['exercises'])} alıştırma")
    print(f"  - Kelime: {sum(1 for e in ex_data['exercises'] if e.get('type')=='kelime')}")
    print(f"  - Cümle:  {sum(1 for e in ex_data['exercises'] if e.get('type') in ('cümle','cumle'))}")
    print(f"  - Tekerleme: {sum(1 for e in ex_data['exercises'] if e.get('type')=='tekerleme')}")
    print(f"  - Paragraf: {sum(1 for e in ex_data['exercises'] if e.get('type')=='paragraf')}")
    print(f"\nKaydedildi: {EX_PATH}")


if __name__ == "__main__":
    main()
