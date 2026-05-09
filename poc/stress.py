"""Türkçe vurgu yeri tahmini.

Kelime tek tek alınır, hangi hecede vurgu olması gerektiği döner (0-tabanlı).
Sözlük + heuristik karışımı. Stres sözlüğü genişledikçe daha doğru çalışır.

Kurallar (öncelik sırasına göre):
  1. Manuel istisna sözlüğü
  2. Yer adı listesi → ilk hece
  3. -ya ile biten yer adı listesi → sondan bir önceki hece
  4. Zarf/bağlaç listesi → ilk hece
  5. Varsayılan: son hece
"""

from __future__ import annotations

import re

from lexicon import LEX, tr_lower

VOWELS = set("aeıioöuüâîû")


def syllabify(word: str) -> list[str]:
    """Türkçeye uygun basit hece bölme: V, CV, VC, CVC, CCVC desenleri.
    Heuristic: ünlü sayısı = hece sayısı; sınırlar bir önceki ünlüden sonraki ilk
    ünsüze kadardır."""
    w = tr_lower(word.strip())
    if not w:
        return []

    # Ünlü pozisyonları
    vowel_idx = [i for i, c in enumerate(w) if c in VOWELS]
    if not vowel_idx:
        return [w]

    syllables: list[str] = []
    prev = 0
    for k, vi in enumerate(vowel_idx):
        # Bir sonraki ünlü
        next_vi = vowel_idx[k + 1] if k + 1 < len(vowel_idx) else None
        if next_vi is None:
            # Son hece
            syllables.append(w[prev:])
            break
        # vi ile next_vi arasındaki ünsüzler
        between = w[vi + 1:next_vi]
        if len(between) <= 1:
            # Sınır ünlüden hemen sonra: ünsüz bir sonraki heceye gider (CV)
            syllables.append(w[prev:vi + 1])
            prev = vi + 1
        else:
            # CC arası: ortadan böl (örn 'bul-mak')
            mid = vi + 1 + (len(between) // 2)
            syllables.append(w[prev:mid])
            prev = mid
    return syllables


def stress_index(word: str) -> int:
    """Kelimenin hangi hecesi vurgulu (0-tabanlı). Hece bulunamazsa -1."""
    w = tr_lower(re.sub(r"[^\wçğışöü]", "", word))
    if not w:
        return -1

    # 1) Manuel istisna
    manual = LEX.manual_stress(w)
    if manual is not None:
        return manual

    sylls = syllabify(w)
    n = len(sylls)
    if n == 0:
        return -1
    if n == 1:
        return 0

    # 2) Yer adı (ilk hece)
    if LEX.is_yer_adi(w):
        return 0
    # 3) -ya ile biten yer adı (sondan bir önceki)
    if LEX.is_yer_adi_ya(w):
        return n - 2
    # 4) Zarf/bağlaç
    if LEX.is_zarf_baglac(w):
        return 0
    # 5) Varsayılan: son hece
    return n - 1


def stress_info(word: str) -> dict:
    """Hece + vurgu bilgisi yapısı."""
    sylls = syllabify(word)
    idx = stress_index(word)
    return {
        "word": word,
        "syllables": sylls,
        "stress_index": idx,
        "stressed_syllable": sylls[idx] if 0 <= idx < len(sylls) else "",
    }


if __name__ == "__main__":
    samples = [
        "merhaba", "kalkacağım", "ankara", "sakarya", "kütahya",
        "yalnız", "ancak", "şimdi", "hangi", "lokanta",
        "kelimeler", "diksiyon", "öğretmen", "kâğıt", "düşünüyorum",
    ]
    for w in samples:
        info = stress_info(w)
        marked = "-".join(
            f"[{s}]" if i == info["stress_index"] else s
            for i, s in enumerate(info["syllables"])
        )
        print(f"  {w:18s}  {marked}")
