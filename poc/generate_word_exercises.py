"""693 kelime indeksinden en oğretici olanları seçip exercises.json'a
ekle. Filtre: ğ içeren, uzun ünlü işareti olan, lexicon'da bilinen,
en az 0.7 skorlu eğitmen örneği olan kelimeler.

Cikti: data/exercises/exercises.json (mevcut alıştırmaların altına eklenir)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "data" / "knowledge" / "word_clips_index.json"
EXERCISES_PATH = REPO_ROOT / "data" / "exercises" / "exercises.json"
LEX_G2P = REPO_ROOT / "data" / "lexicon" / "g2p_pairs.json"


def load_lexicon_words() -> set[str]:
    """g2p_pairs.json'da kayıtlı kelimeleri (öğreten için kıymetli) çıkar."""
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


def is_pedagogically_useful(word: str, occs: list[dict], lex_words: set[str]) -> tuple[bool, list[str]]:
    """Bu kelime alıştırma olmaya değer mi? Sebepleri de döndür."""
    reasons = []
    w_low = word.lower()

    # En iyi örneğin skoru
    best_score = max((o.get("score", 0) for o in occs), default=0)
    best_dur = max((o.get("duration_s", 0) for o in occs), default=0)

    # Ses kalitesi yetersizse atla
    if best_score < 0.6 or best_dur < 0.15:
        return False, []

    # Kriterler:
    if w_low in lex_words:
        reasons.append("sözlük")
    if any(c in word for c in "âîû"):
        reasons.append("uzun-ünlü")
    if "ğ" in w_low:
        reasons.append("ğ-silme")
    # Yaygın hata yapılan kelimeler (R/H yutulması adayları)
    if w_low.endswith("yor") or w_low.endswith("yorsun") or w_low.endswith("yorlar"):
        reasons.append("R-yutulması-adayı")
    if "h" in w_low and len(w_low) >= 4:
        # h içerip 4+ harf — H yutulma riski
        reasons.append("H-yutulması-adayı")
    # Çok kısa veya sık ek bağlamayan kelimeler hariç (tek heceli, yardımcı)
    if len(w_low) <= 3:
        return False, []

    # En az 1 sebep olmalı, yoksa skip
    return (len(reasons) > 0), reasons


def make_focus(reasons: list[str]) -> str:
    if "uzun-ünlü" in reasons:
        return "uzun ünlü (â/î/û)"
    if "ğ-silme" in reasons:
        return "yumuşak g (ğ silinir, ünlü uzar)"
    if "R-yutulması-adayı" in reasons:
        return "-yor ekinde R'nin korunması"
    if "H-yutulması-adayı" in reasons:
        return "h sesinin yutulmaması"
    return "telaffuz pratiği"


def difficulty_for(word: str, reasons: list[str]) -> int:
    score = 1
    if "uzun-ünlü" in reasons: score += 1
    if "ğ-silme" in reasons: score += 1
    if len(word) > 7: score += 1
    if len(word) > 12: score += 1
    return min(5, score)


def main() -> None:
    if not INDEX_PATH.exists():
        print(f"Index yok: {INDEX_PATH}")
        return
    with open(INDEX_PATH, encoding="utf-8") as f:
        index = json.load(f)

    lex_words = load_lexicon_words()
    print(f"Lexicon kelimeleri: {len(lex_words)}")
    print(f"Index kelime sayısı: {len(index)}")

    candidates: list[tuple[str, list[dict], list[str]]] = []
    for key, occs in index.items():
        # En sık kayda alınan formu sergile
        word = occs[0].get("context", "").split()
        # Anahtar lowercase normalize edilmiş; eğer occ'larda original word varsa onu al
        # word_clips_index'te orig word saklanmış mı? Not: build_word_clips_index normalize edilmiş key kullanıyor
        # Burada key'i kullanırız ama capitalize: ilk harf büyük (cümle başı kelimeler gibi)
        clean = key.strip()
        if not clean:
            continue
        ok, reasons = is_pedagogically_useful(clean, occs, lex_words)
        if ok:
            candidates.append((clean, occs, reasons))

    # En iyilerden başlayarak sırala (skor + sebep sayısı)
    candidates.sort(
        key=lambda c: (-len(c[2]), -max(o.get("score", 0) for o in c[1]))
    )

    print(f"\n{len(candidates)} aday kelime bulundu (en iyi 60'a kadar alınacak)")
    selected = candidates[:60]
    print("\nSeçilenler:")
    for w, occs, rs in selected[:20]:
        best = max(occs, key=lambda o: o.get("score", 0))
        print(f"  {w:20s}  ({', '.join(rs):30s})  skor={best['score']}")
    if len(selected) > 20:
        print(f"  ... +{len(selected)-20} daha")

    # Mevcut alıştırma listesini yükle
    with open(EXERCISES_PATH, encoding="utf-8") as f:
        ex_data = json.load(f)
    existing = ex_data["exercises"]
    existing_texts = {ex["text"].lower() for ex in existing}

    new_exercises = []
    next_idx = max(
        [int(re.search(r"(\d+)$", ex["id"]).group(1))
         for ex in existing if "kelime-" in ex["id"]],
        default=100,
    ) + 1

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
            "notes": f"Diksiyon eğitmen videosundan ({len(occs)} örnek). Kategoriler: {', '.join(reasons)}",
            "ref_source": "word_clip",  # /reference yerine /word-clip kullanılsın
        })

    print(f"\n{len(new_exercises)} yeni kelime alıştırması eklendi")
    ex_data["exercises"] = existing + new_exercises
    with open(EXERCISES_PATH, "w", encoding="utf-8") as f:
        json.dump(ex_data, f, ensure_ascii=False, indent=2)
    print(f"Kaydedildi: {EXERCISES_PATH}")


if __name__ == "__main__":
    main()
