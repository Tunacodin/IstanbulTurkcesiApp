"""
Egitmen tarzi geri bildirim ureteci.

Per-karakter skorlari + hedef metni alir, Turkce diksiyon terimleriyle
yapilandirilmis geri bildirim verir.

Ornek cikti:
  {
    "overall_score": 0.82,
    "verdict": "iyi",
    "issues": [
      {"position": 3, "char": "ğ", "score": 0.31,
       "advice": "Bu ‘ğ’ sessizdir, önündeki ünlüyü uzatır. ‘daa-cağız’ gibi düşün."}
    ],
    "feedback_text": "İyi! Tek noktaya dikkat: ‘ğ’ harfi..."
  }
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Optional

from align_and_score import CharSegment, SCORE_THRESHOLD
from g2p import LONG_VOWELS, phoneme_info, pronunciation_form, tr_lower
from lexicon import LEX
from prosody import NaturalnessReport, ProsodyComparison, StressMeasurement

PROSODY_SEVERITY_THRESHOLD = 0.25  # bu üzeri "vurgu farki" olarak isaretlenir
LONG_VOWEL_DURATION_RATIO = 1.4    # â/î/û en az ortalama ünlü süresinin 1.4x'i olmalı
TRANSCRIPTION_MISMATCH_FLOOR = 0.10  # tam mismatch olsa bile skor bu kadarın altına inmesin
# Naturalness her sorun başına çarpan ceza (0.85 = -%15)
NATURALNESS_PENALTY_PER_ISSUE = 0.85
NATURALNESS_MIN_FACTOR = 0.55       # naturalness factor bu altına inmesin

# Diksiyon-kritik ünsüz değişim çiftleri (ötümlü ↔ ötümsüz).
# Bu çiftler İstanbul Türkçesi standart dışı; Anadolu ağzına özgü.
DIKSIYON_KRITIK_PAIRS: set[tuple[str, str]] = {
    ("k", "g"), ("g", "k"),
    ("t", "d"), ("d", "t"),
    ("p", "b"), ("b", "p"),
    ("ç", "c"), ("c", "ç"),
    ("s", "z"), ("z", "s"),
    ("f", "v"), ("v", "f"),
    ("k", "v"),  # 'kuş' → 'vuş' tipi büyük hata
    ("g", "ğ"), ("ğ", "g"),  # gagasıyla → gağasıyla
}

# Kelime hatası tavanları — N kelime yanlışsa skor en fazla şu kadar olabilir.
WORD_ERROR_CAPS = {1: 0.70, 2: 0.50, 3: 0.30}
WORD_ERROR_FLOOR = 0.10  # 4+ kelime hatası varsa skor en fazla bu


# Türkçe karakterlere özgü diksiyon notları.
# Anahtar: hedef harf. Değer: o harfle ilgili genel İstanbul Türkçesi diksiyon notu.
LETTER_NOTES: dict[str, str] = {
    "ğ": "‘ğ’ harfi sessizdir; önündeki ünlüyü hafifçe uzatır. Boğazdan çıkarılmaya çalışılmaz.",
    "â": "‘â’ uzun ve ince okunur; ‘kâr’ sözcüğünü ‘kaar’ gibi düşün, ‘kar’ (yağmur) ile karıştırma.",
    "î": "‘î’ uzun ve ince okunur. Tıpkı ‘â’ gibi vurgulu ve uzun.",
    "û": "‘û’ uzun ve ince okunur; ‘sükût’ gibi.",
    "h": "‘h’ sesi yutulmaz; özellikle sözcük sonunda hafifçe duyulmalı.",
    "r": "Sözcük sonundaki ‘r’ titretilir ama abartılmaz. Kuvvetli ‘rrr’ değil, kontrollü tek titreşim.",
    "ı": "‘ı’ ile ‘i’ ayrımı net olmalı. ‘ı’ arka, kısık, dudaksız.",
    "i": "‘i’ ön, ince, dudaksız. ‘ı’ ile karıştırma.",
    "e": "Bazı kelimelerde ‘e’ kapalı (‘é’) okunur — ‘ben, sen, gel’ gibi. Ağız aralığını biraz daralt.",
    "ş": "‘ş’ sesinde dudaklar hafifçe yuvarlak; dilin ucu damağa yaklaşır ama değmez.",
    "s": "‘s’ keskin ve net; ‘ş’ ile karıştırma — dudaklar düz olmalı.",
    "ç": "‘ç’ sesinde patlayıcı + ıslıklı bileşim var; net ve kısa olmalı.",
    "c": "‘c’ sesi ‘ç’den daha yumuşak, sesli (ötümlü). ‘canım’ gibi.",
    "v": "‘v’ alt dudak üst dişe değecek şekilde, sesli; ‘f’ gibi fısıltılı olmamalı.",
    "y": "‘y’ kayan bir geçiş sesidir; öncesindeki ünlüyle birleşir, kesilmez.",
    "n": "Söz sonu ‘n’ açık ve net olmalı; ‘m’ye dönüşmemeli.",
    "k": "‘k’ ön ünlülerden önce (‘ki, ke, kö’) damaksıl olmalı; arka ünlülerden önce daha gırtlaksıl.",
    "g": "‘g’ sesi sesli (ötümlü); ‘k’ ile karıştırılmamalı.",
    "p": "‘p’ patlayıcı ve nefesli; net çıkmalı.",
    "b": "‘b’ ‘p’nin ötümlüsü; dudaklar tam kapanmalı.",
    "t": "‘t’ patlayıcı, dil ucu üst dişlerin arkasına; ‘d’den daha sert.",
    "d": "‘d’ ‘t’nin ötümlüsü; aynı yerden çıkar ama ses telleri titreşir.",
}

# Belirli iki-harfli sorunlu kombinasyonlar.
DIGRAPH_NOTES: dict[str, str] = {
    "ğa": "‘ğa’: ‘ğ’ silinir, ‘a’ uzar. ‘bağa’ → ‘baa’ gibi.",
    "ğı": "‘ğı’: ‘ğ’ silinir, ‘ı’ uzar.",
    "ğu": "‘ğu’: ‘ğ’ silinir, ‘u’ uzar.",
    "ğe": "‘ğe’: ‘ğ’ silinir, ‘e’ uzar. ‘değer’ → ‘deer’.",
    "ği": "‘ği’: ‘ğ’ silinir, ‘i’ uzar.",
    "ğü": "‘ğü’: ‘ğ’ silinir, ‘ü’ uzar.",
}


@dataclass
class Issue:
    position: int
    char: str
    score: float
    advice: str
    kind: str = "telaffuz"  # "telaffuz" | "vurgu" | "uzun-unlu" | "kelime"
    word_index: int = -1
    target_word: str = ""
    spoken_word: str = ""


@dataclass
class FeedbackResult:
    overall_score: float
    verdict: str  # "mukemmel" | "iyi" | "gelistirilebilir" | "tekrar"
    target_text: str
    issues: list[Issue] = field(default_factory=list)
    feedback_text: str = ""
    transcription: Optional[str] = None
    transcription_match: float = 1.0  # 0-1, target vs transcription benzerligi

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 3),
            "verdict": self.verdict,
            "target_text": self.target_text,
            "transcription": self.transcription,
            "transcription_match": round(self.transcription_match, 3),
            "issues": [
                {
                    "position": i.position,
                    "char": i.char,
                    "score": round(i.score, 3),
                    "advice": i.advice,
                    "kind": i.kind,
                    "word_index": i.word_index,
                    "target_word": i.target_word,
                    "spoken_word": i.spoken_word,
                }
                for i in self.issues
            ],
            "feedback_text": self.feedback_text,
        }


def _prosody_advice(dur_r: float, f0_r: float, en_r: float) -> str:
    """Sapma oranlarina bakarak vurgu/sure tarzi tavsiye ureti."""
    parts: list[str] = []
    if dur_r > 1.25:
        parts.append("bu sesi gerektiğinden uzun tutmuşsun")
    elif dur_r < 0.8:
        parts.append("bu sesi gerektiğinden kısa kesmişsin")
    if f0_r > 1.15:
        parts.append("perdeyi gereğinden yüksek vermişsin")
    elif f0_r < 0.85:
        parts.append("perdeyi gereğinden alçak vermişsin")
    if en_r > 1.25:
        parts.append("bu sesi gereğinden vurgulu söylemişsin")
    elif en_r < 0.8:
        parts.append("bu sesi gereğinden zayıf söylemişsin")
    if not parts:
        return "Vurgu profilinde küçük bir sapma var."
    return "Referansa göre: " + ", ".join(parts) + "."


def _verdict_for(score: float) -> str:
    if score >= 0.90:
        return "mukemmel"
    if score >= 0.75:
        return "iyi"
    if score >= 0.55:
        return "gelistirilebilir"
    return "tekrar"


def _verdict_text(verdict: str) -> str:
    return {
        "mukemmel": "Mükemmel! Telaffuzun çok temiz.",
        "iyi": "İyi gidiyor. Ufak ayrıntılara dikkat:",
        "gelistirilebilir": "Bazı sesler net çıkmamış. Şu noktalara odaklan:",
        "tekrar": "Bir kez daha dene. Şu sesleri özellikle çalış:",
    }[verdict]


def _advice_for_segment(
    segment: CharSegment,
    target_text: str,
    position: int,
    phon_infos: list,
) -> Optional[str]:
    """Karakter ve baglam icin Turkce diksiyon onerisi uret."""
    char = tr_lower(segment.char)

    # 1) G2P phoneme_info: kelime baglaminda not varsa onu kullan (ğ sessiz, â uzun, ...)
    if 0 <= position < len(phon_infos):
        info = phon_infos[position]
        if info.note:
            # Telaffuz formuyla zenginleştir: "yapacağım kelimesi 'yapacaım' olarak okunur."
            try:
                word = _word_at(target_text, position)
            except Exception:
                word = ""
            if word and any(c in "ğâîû" for c in word):
                pron = pronunciation_form(word)
                if pron != tr_lower(word):
                    return f"{info.note} ‘{word}’ kelimesi ‘{pron}’ olarak okunur."
            return info.note

    # 2) Bigram (örn. 'ğa' düşmesi)
    if position + 1 < len(target_text):
        digraph = tr_lower(char + target_text[position + 1])
        if digraph in DIGRAPH_NOTES:
            return DIGRAPH_NOTES[digraph]

    # 3) Genel harf notu
    if char in LETTER_NOTES:
        return LETTER_NOTES[char]

    return f"‘{char}’ sesi belirsiz çıktı, ağız konumuna dikkat ederek tekrar dener misin?"


def _word_at(text: str, position: int) -> str:
    """Cumlede pozisyondaki karakterin ait oldugu kelimeyi dondur."""
    if position < 0 or position >= len(text):
        return ""
    # Beyaz-bosluga kadar geri+ileri yuru
    start = position
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    end = position
    while end < len(text) and not text[end].isspace():
        end += 1
    return text[start:end]


def _strip_long_marks(text: str) -> str:
    """â/î/û -> a/i/u; transcription benzerligi icin (uzunluk farki sure
    kontrolüyle ayrica yakalanir, karakterde cezalandirmaya gerek yok)."""
    return (text.replace("â", "a")
                .replace("î", "i")
                .replace("û", "u"))


def _transcription_similarity(target: str, transcription: str) -> float:
    """Karakter-seviyesi benzerlik (geriye uyumluluk için tutuldu)."""
    a = _strip_long_marks(tr_lower(target).strip())
    b = _strip_long_marks(tr_lower(transcription).strip())
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _normalize_word(w: str) -> str:
    """Kelime karşılaştırma için noktalama at, küçük harfe çevir, uzun-işaret düşür."""
    import re
    w = tr_lower(w)
    w = _strip_long_marks(w)
    w = re.sub(r"[^\wçğışöü]", "", w)
    return w


def _detect_critical_substitutions(target_word: str, trans_word: str) -> list[tuple[str, str]]:
    """İki kelime arasındaki diksiyon-kritik ünsüz değişimlerini bul.
    Sadece replace operasyonlarına bakar; ekleme/silme genel hatadır."""
    a = _normalize_word(target_word)
    b = _normalize_word(trans_word)
    sm = difflib.SequenceMatcher(None, a, b)
    subs: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "replace":
            continue
        # Karakter karakter eşleştir (eşit uzunluk değilse min al)
        for tc, sc in zip(a[i1:i2], b[j1:j2]):
            if (tc, sc) in DIKSIYON_KRITIK_PAIRS:
                subs.append((tc, sc))
    return subs


def _word_level_match(target: str, transcription: str) -> dict:
    """Kelime tabanlı eşleşme — yanlış söylenmiş kelimeleri çıkartır.
    mismatches: [(target_word, spoken_word, target_word_index_in_original_text)]"""
    target_words = [w for w in target.strip().split() if w]
    trans_words = [w for w in transcription.strip().split() if w]
    if not target_words:
        return {"word_match": 0.0, "mismatches": [], "total": 0, "matched": 0}

    target_norm = [_normalize_word(w) for w in target_words]
    trans_norm = [_normalize_word(w) for w in trans_words]

    sm = difflib.SequenceMatcher(None, target_norm, trans_norm)
    matched = 0
    # mismatches: (target_word, spoken_word, target_word_index)
    mismatches: list[tuple[str, str, int]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            matched += i2 - i1
            continue
        if tag == "replace":
            t_slice = target_words[i1:i2]
            s_slice = trans_words[j1:j2]
            n = max(len(t_slice), len(s_slice))
            for k in range(n):
                tw = t_slice[k] if k < len(t_slice) else ""
                sw = s_slice[k] if k < len(s_slice) else ""
                tidx = (i1 + k) if k < len(t_slice) else -1
                mismatches.append((tw, sw, tidx))
        elif tag == "delete":
            for offset, tw in enumerate(target_words[i1:i2]):
                mismatches.append((tw, "", i1 + offset))
        elif tag == "insert":
            # Eklenen kelimelerin target'ta indexi yok — i1 (sonraki kelimenin pozisyonu) varsayıyoruz
            for sw in trans_words[j1:j2]:
                mismatches.append(("", sw, i1 if i1 < len(target_words) else -1))

    total = len(target_words)
    word_match = matched / total if total else 0.0
    return {
        "word_match": word_match,
        "mismatches": mismatches,
        "total": total,
        "matched": matched,
    }


def _long_vowel_duration_issues(
    segments: list[CharSegment], target_text: str, visible_positions: list[int],
    text_chars_lower: str,
) -> list[Issue]:
    """â/î/û olan segmentlerin sürelerini median segment süresiyle kıyasla.
    Yeterince uzun degilse 'uzun olmali' issue dondur."""
    real = [s for s in segments if s.char != "|"]
    if not real:
        return []
    durations = sorted(s.end_s - s.start_s for s in real)
    median_dur = durations[len(durations) // 2]
    # Ortalama ünlü süresini de hesapla — varsa tercihen onu kullan
    plain_vowel_durations = [
        (s.end_s - s.start_s) for s in real
        if tr_lower(s.char) in {"a", "e", "i", "ı", "o", "ö", "u", "ü"}
    ]
    if plain_vowel_durations:
        baseline = sum(plain_vowel_durations) / len(plain_vowel_durations)
    else:
        baseline = median_dur  # plain ünlü yoksa medyan tüm segment süresi

    issues: list[Issue] = []
    for s in real:
        # ÖNEMLİ: orijinal target_char'a bak (â/î/û), alignment char'ına değil (a/i/u fallback olabilir)
        original = s.target_char or s.char
        if original not in LONG_VOWELS:
            continue
        dur = s.end_s - s.start_s
        if dur >= baseline * LONG_VOWEL_DURATION_RATIO:
            continue  # yeterince uzun
        try:
            position = next(
                p for p in visible_positions if text_chars_lower[p] == original
            )
        except StopIteration:
            position = -1
        ratio = dur / max(baseline, 1e-3)
        issues.append(
            Issue(
                position=position,
                char=original,
                score=min(0.6, max(0.0, ratio / LONG_VOWEL_DURATION_RATIO)),
                advice=(
                    f"‘{original}’ uzun ve ince okunmalı; çok kısa kesmişsin. "
                    f"Süresini ortalama sesin ~1.5 katına çıkar."
                ),
                kind="uzun-unlu",
            )
        )
    return issues


def make_feedback(
    segments: list[CharSegment],
    target_text: str,
    prosody: Optional[ProsodyComparison] = None,
    transcription: Optional[str] = None,
    naturalness: Optional[NaturalnessReport] = None,
    stress_measurements: Optional[list[StressMeasurement]] = None,
) -> FeedbackResult:
    real_segments = [s for s in segments if s.char != "|"]
    if not real_segments:
        return FeedbackResult(
            overall_score=0.0,
            verdict="tekrar",
            target_text=target_text,
            feedback_text="Sesin çok belirsiz, tekrar kayıt al.",
            transcription=transcription,
            transcription_match=0.0,
        )

    # Uzun ünlü süre kontrolünü erken hesapla; segment skorlarını
    # min(alignment_score, long_vowel_score) ile birleştir.
    text_chars_lower_pre = tr_lower(target_text)
    visible_pre = [i for i, c in enumerate(text_chars_lower_pre) if not c.isspace()]
    early_lv_issues = _long_vowel_duration_issues(
        segments, target_text, visible_pre, text_chars_lower_pre,
    )
    if early_lv_issues:
        # Hangi segment'lere ceza uygulanacak? target_char'a göre eşleştir.
        # Bir kerelik tüketim için seg id'lerine göre map
        penalty_by_target_char_index: dict[int, float] = {}
        # Issue'lar zaten "ilk eşleşmeyi" alıyor, sıraya göre uyguluyoruz:
        seen_long_vowel_segs: set[int] = set()
        for issue in early_lv_issues:
            for idx, seg in enumerate(real_segments):
                if idx in seen_long_vowel_segs:
                    continue
                original = seg.target_char or seg.char
                if original == issue.char:
                    seen_long_vowel_segs.add(idx)
                    seg.score = min(seg.score, issue.score)
                    break

    alignment_score = sum(s.score for s in real_segments) / len(real_segments)
    # Kelime seviyesi eşleşme: hangi kelimeleri yanlış söyledi?
    if transcription is not None:
        wm_data = _word_level_match(target_text, transcription)
        word_match = wm_data["word_match"]
        word_mismatches = wm_data["mismatches"]
        match_ratio = _transcription_similarity(target_text, transcription)  # legacy ölçüm
    else:
        word_match = 1.0
        word_mismatches = []
        match_ratio = 1.0

    # Final skor: kelime tabanlı eşleşme + alignment.
    # Kelime tabanlı eşleşme sertçe çarpan olarak uygulanır.
    blended_match = max(TRANSCRIPTION_MISMATCH_FLOOR, word_match)
    overall = alignment_score * blended_match

    # Kelime hatası sayısına göre TAVAN — alignment yüksek olsa bile skor düşer.
    n_word_errors = len(word_mismatches)
    if n_word_errors >= 4:
        overall = min(overall, WORD_ERROR_FLOOR)
    elif n_word_errors in WORD_ERROR_CAPS:
        overall = min(overall, WORD_ERROR_CAPS[n_word_errors])

    # Naturalness cezası — monoton, tutuk, hece hece söyleme vb.
    naturalness_factor = 1.0
    if naturalness is not None and naturalness.issues:
        for _ in naturalness.issues:
            naturalness_factor *= NATURALNESS_PENALTY_PER_ISSUE
        naturalness_factor = max(naturalness_factor, NATURALNESS_MIN_FACTOR)
        overall *= naturalness_factor

    verdict = _verdict_for(overall)

    # En sorunlu en fazla 5 ses
    bad = [s for s in real_segments if s.score < SCORE_THRESHOLD]
    bad.sort(key=lambda s: s.score)
    bad = bad[:5]

    issues: list[Issue] = []
    # G2P phoneme_info'yi target_text uzerinde bir kez hesapla.
    phon_infos = phoneme_info(target_text)
    # phon_infos'taki sira target_text'teki goz onunde tutulan karakter sirasi.
    text_chars_lower = tr_lower(target_text)
    visible_positions = [i for i, c in enumerate(text_chars_lower) if not c.isspace()]
    # Long vowel issue'larin zaten kapsadigi karakter+poziisyonlar
    long_vowel_positions = {iss.position for iss in early_lv_issues if iss.position >= 0}
    long_vowel_chars = {tr_lower(iss.char) for iss in early_lv_issues}
    consumed_positions: set[int] = set(long_vowel_positions)
    for seg in bad:
        char_for_lookup = tr_lower(seg.target_char or seg.char)
        # Eger bu karakter icin zaten uzun-unlu issue varsa, dublike etme
        if char_for_lookup in long_vowel_chars:
            continue
        try:
            position = next(
                p for p in visible_positions
                if text_chars_lower[p] == char_for_lookup
                and p not in consumed_positions
            )
        except StopIteration:
            position = -1
        if position >= 0:
            consumed_positions.add(position)
        # Issue'da target_char göster (kullanıcıya orijinal harfi söyle)
        display_char = seg.target_char or seg.char
        advice = _advice_for_segment(seg, target_text, position, phon_infos) or ""
        issues.append(
            Issue(
                position=position,
                char=display_char,
                score=seg.score,
                advice=advice,
            )
        )

    # Uzun ünlü kontrolleri ilk hesaplamada bulundu; tekrarlamadan ekle.
    issues.extend(early_lv_issues)

    # Kelime bazlı issue'lar — yanlış söylenmiş her kelime için ayrı issue
    for target_word, trans_word, word_idx in word_mismatches:
        if not target_word and not trans_word:
            continue
        issue_kind = "kelime"
        if target_word and not trans_word:
            advice = f"‘{target_word}’ kelimesini söylemedin/atladın."
        elif trans_word and not target_word:
            advice = f"Fazladan ‘{trans_word}’ kelimesi söyledin."
        else:
            # 1) Bilinen diksiyon kalıpları (R-yutulması, H-yutulması)
            pattern_match = LEX.matches_error_pattern(target_word, trans_word)
            if pattern_match:
                advice = (
                    f"‘{target_word}’ yerine ‘{trans_word}’ söyledin. "
                    f"{pattern_match['kural']}"
                )
                issue_kind = pattern_match["kind"]  # "r_yutulmasi" / "h_yutulmasi"
            else:
                # 2) Diksiyon-kritik ünsüz değişimi
                subs = _detect_critical_substitutions(target_word, trans_word)
                if subs:
                    pretty = ", ".join(f"{t}→{s}" for t, s in subs)
                    advice = (
                        f"‘{target_word}’ yerine ‘{trans_word}’ söyledin — "
                        f"diksiyon-kritik ünsüz değişimi var ({pretty}). "
                        f"Bu Anadolu ağzına özgü; İstanbul Türkçesi'nde "
                        f"{', '.join(t for t, _ in subs)} olarak çıkmalı."
                    )
                    issue_kind = "kritik_unsuz"
                else:
                    advice = f"‘{target_word}’ kelimesini ‘{trans_word}’ olarak söyledin. Tekrar dene."
                    issue_kind = "kelime"
        issues.append(Issue(
            position=-1,
            char=target_word or trans_word,
            score=0.0,
            advice=advice,
            kind=issue_kind,
            word_index=word_idx,
            target_word=target_word,
            spoken_word=trans_word,
        ))

    # Naturalness sorunlari — referansa bagimsiz uyarilar
    if naturalness is not None:
        kind_map = {
            "monotonik": ("dogallik", "Konuşman düz/monoton"),
            "yavaş": ("dogallik", "Tutuk / yavaş konuşma"),
            "hızlı": ("dogallik", "Çok hızlı konuşma"),
            "hece": ("dogallik", "Hece hece söyleme"),
        }
        # naturalness.issues düz string listesi; her birini ayrı issue olarak ekle
        for natural_issue in naturalness.issues:
            kind = "dogallik"
            char_marker = "♪"
            if "monoton" in natural_issue.lower():
                char_marker = "♪"
            elif "yavaş" in natural_issue.lower() or "tutuk" in natural_issue.lower():
                char_marker = "🐢"
            elif "hızlı" in natural_issue.lower():
                char_marker = "🐇"
            elif "hece hece" in natural_issue.lower() or "duraklama" in natural_issue.lower():
                char_marker = "✂"
            issues.append(Issue(
                position=-1,
                char=char_marker,
                score=naturalness_factor,
                advice=natural_issue,
                kind=kind,
            ))

    # Vurgu yeri ölçümleri — beklenen ile kıyasla, sapma varsa issue
    if stress_measurements:
        for sm in stress_measurements:
            if not sm.confident or sm.measured_stress_idx == sm.expected_stress_idx:
                continue
            # Sapma var
            expected = sm.syllables[sm.expected_stress_idx] if 0 <= sm.expected_stress_idx < len(sm.syllables) else "?"
            measured = sm.syllables[sm.measured_stress_idx] if 0 <= sm.measured_stress_idx < len(sm.syllables) else "?"
            issues.append(Issue(
                position=-1,
                char=sm.word,
                score=0.4,
                advice=(
                    f"‘{sm.word}’ kelimesinde vurguyu ‘{measured}’ hecesinde yapmışsın; "
                    f"İstanbul Türkçesi'nde ‘{expected}’ vurgulanmalı. "
                    f"Hece sırası: {'-'.join(sm.syllables)}"
                ),
                kind="vurgu_yeri",
                target_word=sm.word,
            ))

    # Prosody varsa, en kotu vurgu sapmalarini da issue olarak ekle.
    if prosody is not None:
        for dev in prosody.biggest_outliers:
            if dev.severity < PROSODY_SEVERITY_THRESHOLD:
                continue
            char_l = tr_lower(dev.char)
            try:
                position = next(p for p in visible_positions if text_chars_lower[p] == char_l)
            except StopIteration:
                position = -1
            issues.append(
                Issue(
                    position=position,
                    char=dev.char,
                    score=1.0 - dev.severity,
                    advice=_prosody_advice(dev.duration_ratio, dev.f0_ratio, dev.energy_ratio),
                    kind="vurgu",
                )
            )

    parts = [_verdict_text(verdict)]
    for it in issues:
        tag = {
            "vurgu": "vurgu",
            "uzun-unlu": "uzun ünlü",
            "kelime": "kelime",
        }.get(it.kind, "ses")
        if it.kind == "kelime":
            parts.append(f"  • {it.advice}")
        else:
            parts.append(f"  • ‘{it.char}’ {tag} (skor: {it.score:.2f}) — {it.advice}")
    if verdict == "mukemmel" and not issues:
        parts.append(f"  Skor: {overall:.2f}")

    return FeedbackResult(
        overall_score=overall,
        verdict=verdict,
        target_text=target_text,
        issues=issues,
        feedback_text="\n".join(parts),
        transcription=transcription,
        transcription_match=match_ratio,
    )
