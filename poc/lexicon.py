"""Lexicon yükleyici — diksiyon eğitim materyalindeki yapılandırılmış veriyi okur.

Kullanım:
    from lexicon import LEX
    print(LEX.exception("değil"))         # 'diil'
    print(LEX.r_yutulmasi("geliyor"))     # 'geliyo'  (bilinen bozuk biçim)
    print(LEX.is_yer_adi("ankara"))       # True
    print(LEX.stress_index("ankara"))     # 0  (ilk hece)
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEX_DIR = REPO_ROOT / "data" / "lexicon"


def _load(name: str) -> dict:
    path = LEX_DIR / name
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def tr_lower(text: str) -> str:
    return text.replace("I", "ı").replace("İ", "i").lower()


@lru_cache(maxsize=1)
def _g2p_pairs() -> dict:
    return _load("g2p_pairs.json")


@lru_cache(maxsize=1)
def _error_patterns() -> dict:
    return _load("error_patterns.json")


@lru_cache(maxsize=1)
def _stress() -> dict:
    return _load("stress_lexicon.json")


def _flatten_g2p() -> dict[str, str]:
    """Tüm g2p kategorilerini tek bir kelime->okunuş haritasına birleştir."""
    out: dict[str, str] = {}
    data = _g2p_pairs()
    for key, group in data.items():
        if not isinstance(group, dict) or key.startswith("_meta"):
            continue
        for k, v in group.items():
            if isinstance(v, str) and not k.startswith("_"):
                out[tr_lower(k)] = v
    return out


@lru_cache(maxsize=1)
def _g2p_flat() -> dict[str, str]:
    return _flatten_g2p()


def _flatten_error_patterns() -> dict[str, dict]:
    """ {target_word: {kind, spoken_form, kural} } şeklinde düz harita."""
    out: dict[str, dict] = {}
    data = _error_patterns()
    for kind, group in data.items():
        if not isinstance(group, dict) or kind.startswith("_"):
            continue
        kural = group.get("kural", "")
        for target, spoken in (group.get("ornekler") or {}).items():
            out[tr_lower(target)] = {"kind": kind, "spoken": spoken, "kural": kural}
    return out


@lru_cache(maxsize=1)
def _error_flat() -> dict[str, dict]:
    return _flatten_error_patterns()


# ---- Public API ----

class LexiconAccess:
    def pronunciation(self, word: str) -> str | None:
        return _g2p_flat().get(tr_lower(word))

    def is_yer_adi(self, word: str) -> bool:
        return tr_lower(word) in set(_stress().get("yer_adlari_ilk_hece", []))

    def is_yer_adi_ya(self, word: str) -> bool:
        return tr_lower(word) in set(_stress().get("ya_ile_biten_yer_sondan_birOnceki", []))

    def is_zarf_baglac(self, word: str) -> bool:
        return tr_lower(word) in set(_stress().get("zarf_baglac_ilk_hece", []))

    def manual_stress(self, word: str) -> int | None:
        return (_stress().get("ozel_istisnalar") or {}).get(tr_lower(word))

    def known_error(self, target_word: str) -> dict | None:
        """Eğer target için bilinen 'bozuk' kullanım örnekleri varsa, o kayıtları döndür."""
        return _error_flat().get(tr_lower(target_word))

    def matches_error_pattern(self, target_word: str, spoken_word: str) -> dict | None:
        """Target ve spoken_word verildiğinde, hata bilinen bir desene uyuyor mu kontrol et.
        Returns: {kind, kural} ya da None."""
        target_l = tr_lower(target_word.strip(",.!?:;"))
        spoken_l = tr_lower(spoken_word.strip(",.!?:;"))

        # 1) Tam liste eşleşmesi
        info = self.known_error(target_l)
        if info and tr_lower(info["spoken"]) == spoken_l:
            return {"kind": info["kind"], "kural": info["kural"]}

        # 2) Pattern-bazlı tespit:
        #    R yutulması: target -yor ile bitiyor, spoken -yo ile bitiyor
        if (target_l.endswith("yor") or target_l.endswith("yorsun") or target_l.endswith("yorlar")
            or target_l.endswith("yormu") or target_l.endswith("yorum")):
            # Sondaki r düşmüş mü?
            if not spoken_l.endswith("r") and target_l.replace("r", "", 1) != target_l:
                # Daha sıkı: target = spoken + 'r' (yaklaşık)
                if _no_r_form(target_l) == spoken_l:
                    grp = _error_patterns().get("r_yutulmasi", {})
                    return {"kind": "r_yutulmasi", "kural": grp.get("kural", "")}

        # 3) H yutulması: target'ta 'h' var, spoken aynı kelime ama 'h' silinmiş
        if "h" in target_l:
            if target_l.replace("h", "") == spoken_l.replace(":", ""):
                grp = _error_patterns().get("h_yutulmasi", {})
                return {"kind": "h_yutulmasi", "kural": grp.get("kural", "")}

        return None


def _no_r_form(word: str) -> str:
    """R-yutulmuş yaklaşık form: kelime sonu 'r' veya kelime içi -yor- kombinasyonundan 'r' düşür."""
    # En basit: kelime sonu r düş
    if word.endswith("r"):
        return word[:-1]
    # 'yor' içinde r düş ('yorsun' -> 'yosun')
    return re.sub(r"yor", "yo", word)


LEX = LexiconAccess()


if __name__ == "__main__":
    print("G2P sözlük boyutu:", len(_g2p_flat()))
    print("Hata desen kayıt sayısı:", len(_error_flat()))
    print()
    for w in ["değil", "kâr", "doğa", "öğretmen", "geliyor"]:
        print(f"  {w:15s} -> {LEX.pronunciation(w)}")
    print()
    pairs = [("geliyor", "geliyo"), ("kahve", "ka:ve"), ("merhaba", "meraba"),
             ("yapıyorsun", "yapıyosun"), ("merhaba", "merhaba")]
    for t, s in pairs:
        m = LEX.matches_error_pattern(t, s)
        print(f"  '{t}' vs '{s}'  -> {m}")
    print()
    for w in ["ankara", "sakarya", "ancak", "merhaba"]:
        print(f"  {w:15s}  yer_adi={LEX.is_yer_adi(w)}  ya={LEX.is_yer_adi_ya(w)}  zarf={LEX.is_zarf_baglac(w)}")
