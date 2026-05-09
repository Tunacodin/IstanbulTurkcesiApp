"""
Turkce Grapheme-to-Phoneme (G2P) modulu.

Yazi <-> standart Istanbul Turkcesi telaffuz formu donusumu + fonem ozellik
tablosu. Diksiyon egitimine yonelik:
  - 'değil' -> 'deil'  (ğ silinir, ünlü ünlüye baglanir)
  - 'kâr'   -> 'kaar'  (â uzun)
  - 'yapacağım' -> 'yapacaım'  (ğ silinir)
  - 'soğuk' -> 'souk'

Iki ana cikti:
  - pronunciation_form(text) -> str            (insan okur sekilde)
  - phoneme_info(text)       -> list[PhonemeInfo]  (segment-bazli ozellikler)

NOT: Wav2Vec2 modeli yazılı formla eğitildiği için forced alignment'ta yazılı
metni kullanmak daha doğru. G2P çıktısı feedback üretiminde, "bu kelimedeki ğ
sessizdir" gibi pedagojik notlar için kullanilir.
"""

from __future__ import annotations

import dataclasses
import re
import unicodedata

VOWELS = set("aeıioöuüâîû")
LONG_VOWELS = set("âîû")          # şapkalı (uzun)
FRONT_VOWELS = set("eiöüâî")
BACK_VOWELS = set("aıouû")
CONSONANTS = set("bcçdfgğhjklmnprsştvyz")

# Yazılışta var olup telaffuzda eriyen/değişen ozel kelimeler.
# Lexicon dosyasından okunur (data/lexicon/g2p_pairs.json).
def _load_exceptions() -> dict[str, str]:
    try:
        from lexicon import _g2p_flat
        return _g2p_flat()
    except Exception:
        return {
            "değil": "diil", "değildir": "diildir",
            "değilim": "diilim", "değilsin": "diilsin",
        }

EXCEPTIONS: dict[str, str] = _load_exceptions()


@dataclasses.dataclass
class PhonemeInfo:
    """Bir karakter / fonem hakkindaki kontekstuel bilgi."""
    char: str           # yazılı karakter
    pron_char: str      # telaffuz karakteri ("ğ" -> ""; "â" -> "a:")
    is_vowel: bool
    is_long: bool       # uzun unlu mu (â/î/û veya ğ ile uzatılmış)
    is_silent: bool     # sesli/yazılı ama duyulmayan
    note: str           # diksiyon notu (varsa)


# ---------- Donusum ----------

def tr_lower(text: str) -> str:
    """Turkce-dogru lowercase (I -> ı, İ -> i)."""
    return (
        text.replace("I", "ı").replace("İ", "i").lower()
    )


def _is_vowel(c: str) -> bool:
    return tr_lower(c) in VOWELS


def _strip_accents(c: str) -> str:
    """â -> a, î -> i, û -> u  (uzunlugu silmeden uzunluk bilgisi kaybolur,
    sadece karşılastirma icin kullan)."""
    nfkd = unicodedata.normalize("NFKD", c)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def _transform_word(word: str) -> str:
    """Tek kelimeyi telaffuz formuna donustur."""
    w = tr_lower(word)
    if w in EXCEPTIONS:
        return EXCEPTIONS[w]

    out: list[str] = []
    chars = list(w)
    i = 0
    while i < len(chars):
        c = chars[i]

        # 1) Şapkalı uzun ünlü: â/î/û -> aa/ii/uu
        if c in LONG_VOWELS:
            out.append(_strip_accents(c) * 2)
            i += 1
            continue

        # 2) ğ kuralı
        if c == "ğ":
            prev_v = out[-1] if out and _is_vowel(out[-1][-1]) else ""
            next_c = chars[i + 1] if i + 1 < len(chars) else ""
            # 2a) V + ğ + V : ğ silinir, önceki ünlü kalır (hafif uzar). Çift V brakmaz.
            if prev_v and next_c and _is_vowel(next_c):
                # ğ silinir, sonraki ünlü zaten gelecek
                i += 1
                continue
            # 2b) V + ğ + (sessiz | sonu) : ünlüyü uzat, ğ sil
            if prev_v and (not next_c or not _is_vowel(next_c)):
                out[-1] = out[-1] + prev_v[-1]  # önceki ünlüyü çift et
                i += 1
                continue
            # 2c) düşük olasılık: kelime başı ğ — koru (yok normalde)
            out.append("ğ")
            i += 1
            continue

        out.append(c)
        i += 1

    return "".join(out)


def pronunciation_form(text: str) -> str:
    """Cumleyi telaffuz formuna donustur (kelime kelime)."""
    if not text:
        return text
    # Önce çok-kelimeli istisnalara bak
    lowered = tr_lower(text)
    for k, v in EXCEPTIONS.items():
        if " " in k and k in lowered:
            lowered = lowered.replace(k, v)
    parts = re.split(r"(\s+)", lowered)
    return "".join(_transform_word(p) if p.strip() else p for p in parts)


# ---------- Fonem ozellikleri ----------

def phoneme_info(text: str) -> list[PhonemeInfo]:
    """Her karakter icin telaffuz ozelliklerini cikar."""
    out: list[PhonemeInfo] = []
    chars = list(tr_lower(text))
    for i, c in enumerate(chars):
        if c.isspace():
            continue

        is_vowel = _is_vowel(c)
        is_long = c in LONG_VOWELS

        # ğ'nin sessizligi
        if c == "ğ":
            prev_v = chars[i - 1] if i > 0 and _is_vowel(chars[i - 1]) else ""
            note = "‘ğ’ sessizdir; önündeki ünlüyü uzatır."
            out.append(PhonemeInfo(
                char=c, pron_char="", is_vowel=False, is_long=False,
                is_silent=True, note=note,
            ))
            continue

        # Şapkalı uzun ünlü
        if is_long:
            out.append(PhonemeInfo(
                char=c, pron_char=_strip_accents(c) * 2,
                is_vowel=True, is_long=True, is_silent=False,
                note=f"‘{c}’ uzun ve ince okunur.",
            ))
            continue

        # ğ'den önceki ünlü uzar
        next_c = chars[i + 1] if i + 1 < len(chars) else ""
        if is_vowel and next_c == "ğ":
            out.append(PhonemeInfo(
                char=c, pron_char=c * 2,
                is_vowel=True, is_long=True, is_silent=False,
                note=f"‘{c}’ ünlüsü, sonraki ‘ğ’ silindiği için uzar.",
            ))
            continue

        out.append(PhonemeInfo(
            char=c, pron_char=c,
            is_vowel=is_vowel, is_long=False, is_silent=False,
            note="",
        ))
    return out


# ---------- CLI test ----------

if __name__ == "__main__":
    samples = [
        "merhaba",
        "değil",
        "kâr",
        "hâlâ",
        "yapacağım",
        "soğuk",
        "dağ",
        "ağzı",
        "değiştir",
        "İstanbul cok güzel",
    ]
    for s in samples:
        pron = pronunciation_form(s)
        print(f"  {s:25s} -> {pron}")
        for info in phoneme_info(s):
            tag = []
            if info.is_silent: tag.append("sessiz")
            if info.is_long: tag.append("uzun")
            tag_s = f" [{', '.join(tag)}]" if tag else ""
            note_s = f"  // {info.note}" if info.note else ""
            print(f"      {info.char}{tag_s}{note_s}")
        print()
