"""
Vurgu / tonlama analizi katmani.

Forced alignment'ten gelen CharSegment'lerle, ses dosyasindan F0 (perde),
RMS enerji ve sure bilgilerini cikarir. Iki ses (kullanici vs egitmen)
ayni metni soyledigi varsayimiyla segment-bazli karsilastirma yapar.

Ana fonksiyonlar:
    - extract_prosody(audio_path, segments) -> ProsodyProfile
    - compare(user, ref) -> ProsodyComparison
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Optional

import librosa
import numpy as np

from align_and_score import CharSegment

SAMPLE_RATE = 16_000
F0_MIN = 75.0   # erkek-kadin ortak alt sinir
F0_MAX = 400.0  # ust sinir
HOP_LENGTH = 256  # ~16ms cozunurluk @ 16kHz


@dataclasses.dataclass
class SegmentProsody:
    char: str
    start_s: float
    end_s: float
    duration_s: float
    f0_mean: float        # Hz, NaN olabilir (sessiz segment)
    energy_rms: float     # 0-1


@dataclasses.dataclass
class ProsodyProfile:
    audio_path: str
    total_duration_s: float
    speaker_mean_f0: float    # konusmacinin genel F0 ortalamasi (Hz)
    speaker_mean_energy: float
    segments: list[SegmentProsody]

    def relative_f0(self, segment_f0: float) -> float:
        """Segmentin F0'inin konusmaci ortalamasina gore orani.
        1.0 = ortalama, 1.2 = vurgulu (yuksek perde), 0.8 = vurgusuz."""
        if not np.isfinite(segment_f0) or self.speaker_mean_f0 <= 0:
            return 1.0
        return float(segment_f0 / self.speaker_mean_f0)

    def relative_energy(self, segment_energy: float) -> float:
        if self.speaker_mean_energy <= 0:
            return 1.0
        return float(segment_energy / self.speaker_mean_energy)


@dataclasses.dataclass
class SegmentDeviation:
    char: str
    user_start_s: float
    duration_ratio: float    # user / ref; 1.0 esit
    f0_ratio: float          # user / ref; 1.0 esit
    energy_ratio: float      # user / ref
    severity: float          # 0 (esit) -> 1 (cok farkli)


@dataclasses.dataclass
class ProsodyComparison:
    overall_severity: float       # 0-1, ortalama deviasyon
    deviations: list[SegmentDeviation]
    biggest_outliers: list[SegmentDeviation]  # severity'ye gore en kotu 3


@dataclasses.dataclass
class NaturalnessReport:
    """Referansa bağımsız konuşma 'doğallık' metrikleri.
    Eşikler: data/lexicon/pace_stats.json (4 diksiyon eğitmen videosundan)."""
    speech_rate_cps: float         # karakter / saniye
    f0_range_semitones: float      # F0 dinamiği (semitone)
    hnr_db: float                  # Harmonik-Gürültü Oranı (dB) — sesin temizliği. >15 iyi, <8 hırıltılı
    intensity_range_db: float      # Ses genliği dinamiği (dB) — vurgu kapasitesi. >12 doğal, <6 düz
    is_monotonic: bool
    is_too_slow: bool
    is_too_fast: bool
    is_choppy: bool
    is_breathy_or_noisy: bool      # HNR düşük
    has_flat_intensity: bool       # genlik dinamiği yok
    intra_word_pauses_s: list[float]
    syllable_duration_cv: float
    issues: list[str]


def _safe_f0(audio: np.ndarray) -> np.ndarray:
    """librosa.pyin ile F0 cikar, np.nan olan yerler sessiz/ovetimsuz."""
    try:
        f0, _, _ = librosa.pyin(
            audio,
            fmin=F0_MIN,
            fmax=F0_MAX,
            sr=SAMPLE_RATE,
            hop_length=HOP_LENGTH,
        )
        return f0
    except Exception:
        return np.array([np.nan])


def _segment_features(
    audio: np.ndarray, f0: np.ndarray, rms: np.ndarray, start_s: float, end_s: float
) -> tuple[float, float]:
    """Bir segment icin (f0_mean, energy_rms) hesapla."""
    # F0 ve RMS aynı hop_length ile çıkarıldı; zaman→frame
    start_f = int(start_s * SAMPLE_RATE / HOP_LENGTH)
    end_f = int(end_s * SAMPLE_RATE / HOP_LENGTH)
    if end_f <= start_f or start_f >= len(f0):
        return float("nan"), 0.0
    f0_slice = f0[start_f:end_f + 1]
    rms_slice = rms[start_f:end_f + 1]
    f0_mean = float(np.nanmean(f0_slice)) if np.any(~np.isnan(f0_slice)) else float("nan")
    energy = float(np.nanmean(rms_slice)) if rms_slice.size else 0.0
    return f0_mean, energy


def extract_prosody(audio_path: Path, segments: list[CharSegment]) -> ProsodyProfile:
    audio, _ = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    f0 = _safe_f0(audio)
    rms = librosa.feature.rms(y=audio, hop_length=HOP_LENGTH)[0]

    # Konuşmacının genel F0 ortalaması — sesli (NaN olmayan) frame'lerin medyanı
    valid_f0 = f0[~np.isnan(f0)] if f0.size else np.array([])
    speaker_mean_f0 = float(np.median(valid_f0)) if valid_f0.size else 0.0
    speaker_mean_energy = float(np.mean(rms)) if rms.size else 0.0

    seg_prosody: list[SegmentProsody] = []
    for s in segments:
        if s.char == "|":
            continue
        f0_mean, energy = _segment_features(audio, f0, rms, s.start_s, s.end_s)
        seg_prosody.append(
            SegmentProsody(
                char=s.char,
                start_s=s.start_s,
                end_s=s.end_s,
                duration_s=s.end_s - s.start_s,
                f0_mean=f0_mean,
                energy_rms=energy,
            )
        )
    return ProsodyProfile(
        audio_path=str(audio_path),
        total_duration_s=float(len(audio) / SAMPLE_RATE),
        speaker_mean_f0=speaker_mean_f0,
        speaker_mean_energy=speaker_mean_energy,
        segments=seg_prosody,
    )


def _ratio(a: float, b: float, default: float = 1.0) -> float:
    if not np.isfinite(a) or not np.isfinite(b) or b <= 0:
        return default
    return float(a / b)


def _severity(dur_r: float, f0_r: float, en_r: float) -> float:
    """Uc oranı 0-1 severity'ye cevir.  Esit = 0,  yuzde 50 sapma ~ 0.5."""
    def dev(r: float) -> float:
        return min(1.0, abs(np.log(max(r, 1e-3))))  # log oran -> simetrik
    return float(np.mean([dev(dur_r), dev(f0_r), dev(en_r)]))


def compare(user: ProsodyProfile, ref: ProsodyProfile) -> ProsodyComparison:
    """
    Iki profili segment-by-segment karsilastir.
    Onsart: user ve ref ayni segment dizisine sahip (ayni metin).

    Önemli: F0 ve enerji konuşmacının ortalamasına göre normalize edilir;
    bu sayede cinsiyet/yaş kaynaklı baz farkı silinir, sadece *vurgu profili*
    karşılaştırılır.
    """
    n = min(len(user.segments), len(ref.segments))
    deviations: list[SegmentDeviation] = []
    for i in range(n):
        u = user.segments[i]
        r = ref.segments[i]
        # Süre toplam konuşma süresine göre normalize (hız farkı silinir)
        u_dur_norm = u.duration_s / user.total_duration_s if user.total_duration_s else 0
        r_dur_norm = r.duration_s / ref.total_duration_s if ref.total_duration_s else 0
        dur_r = _ratio(u_dur_norm, r_dur_norm)
        # F0 ve enerji konuşmacı ortalamasına normalize
        u_f0 = user.relative_f0(u.f0_mean)
        r_f0 = ref.relative_f0(r.f0_mean)
        f0_r = _ratio(u_f0, r_f0)
        u_en = user.relative_energy(u.energy_rms)
        r_en = ref.relative_energy(r.energy_rms)
        en_r = _ratio(u_en, r_en)
        sev = _severity(dur_r, f0_r, en_r)
        deviations.append(
            SegmentDeviation(
                char=u.char,
                user_start_s=u.start_s,
                duration_ratio=round(dur_r, 3),
                f0_ratio=round(f0_r, 3),
                energy_ratio=round(en_r, 3),
                severity=round(sev, 3),
            )
        )
    overall = float(np.mean([d.severity for d in deviations])) if deviations else 0.0
    biggest = sorted(deviations, key=lambda d: -d.severity)[:3]
    return ProsodyComparison(
        overall_severity=round(overall, 3),
        deviations=deviations,
        biggest_outliers=biggest,
    )


def _praat_features(audio_path: Path) -> dict:
    """Praat (parselmouth) ile gelismis fonetik feature'lar.
    HNR (ses temizligi), intensity range (vurgu dinamigi), pitch dinamigi."""
    try:
        import parselmouth
    except Exception:
        return {"hnr_db": 0.0, "intensity_range_db": 0.0, "pitch_std_st": 0.0}

    try:
        sound = parselmouth.Sound(str(audio_path))
        # Pitch — semitone cinsinden std
        pitch = sound.to_pitch(time_step=0.01, pitch_floor=75.0, pitch_ceiling=400.0)
        pitch_values = pitch.selected_array['frequency']
        voiced = pitch_values[pitch_values > 0]
        if voiced.size > 5:
            log2_f0 = np.log2(voiced)
            pitch_std_st = float((np.percentile(log2_f0, 95) - np.percentile(log2_f0, 5)) * 12)
        else:
            pitch_std_st = 0.0

        # Intensity (loudness in dB) — Praat genelde 40-80 dB konuşmada;
        # sessizlik için padding değerleri olabilir.
        intensity = sound.to_intensity(minimum_pitch=75.0)
        int_values = intensity.values.flatten()
        int_values = int_values[~np.isnan(int_values)]
        # Mantıksız değerleri at (Praat sessizlikte garip değerler verebilir)
        int_values = int_values[(int_values > 30.0) & (int_values < 100.0)]
        if int_values.size > 5:
            p10 = float(np.percentile(int_values, 10))
            p90 = float(np.percentile(int_values, 90))
            intensity_range_db = max(0.0, p90 - p10)
        else:
            intensity_range_db = 0.0

        # HNR (Harmonics-to-Noise Ratio)
        try:
            harm = sound.to_harmonicity_cc(time_step=0.01, minimum_pitch=75.0)
            hnr_values = harm.values[0]
            hnr_values = hnr_values[hnr_values != -200]  # silence padding
            hnr_values = hnr_values[~np.isnan(hnr_values)]
            hnr_db = float(np.mean(hnr_values)) if hnr_values.size else 0.0
        except Exception:
            hnr_db = 0.0

        return {
            "hnr_db": hnr_db,
            "intensity_range_db": intensity_range_db,
            "pitch_std_st": pitch_std_st,
        }
    except Exception:
        return {"hnr_db": 0.0, "intensity_range_db": 0.0, "pitch_std_st": 0.0}


def analyze_naturalness(
    audio_path: Path,
    segments: list[CharSegment],
    target_text: str,
) -> NaturalnessReport:
    """Referans gerekmeyen 'naturalness' analizi.
    Kullanıcı tek bir kayıt yaptığında bile çalışır.

    Tespit ettiği sorunlar:
      - Monoton (düz ezgi)
      - Çok yavaş (tutukluk, hece hece söyleme)
      - Çok hızlı
      - Kelime içi pause (heceler arası takılma)
    """
    audio, _ = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    audio, _ = librosa.effects.trim(audio, top_db=30)
    duration_s = float(len(audio) / SAMPLE_RATE)
    # Karakter sayısı (boşluk ve noktalama hariç)
    text_chars = [c for c in target_text if c.isalpha()]
    n_chars = max(1, len(text_chars))

    # 1) Konuşma hızı
    speech_rate_cps = n_chars / max(duration_s, 1e-3)

    # 2) F0 dinamiği — semitone cinsinden
    f0 = _safe_f0(audio)
    valid = f0[np.isfinite(f0) & (f0 > 0)] if f0.size else np.array([])
    if valid.size > 5:
        log2_f0 = np.log2(valid)
        # 5-95 percentile aralığı (semitone)
        p5, p95 = np.percentile(log2_f0, [5, 95])
        f0_range_semitones = float((p95 - p5) * 12)
    else:
        f0_range_semitones = 0.0
    is_monotonic = f0_range_semitones < 1.5

    # 3) Hece (segment) süreleri
    real_segs = [s for s in segments if s.char != "|"]
    seg_durations = [s.end_s - s.start_s for s in real_segs]
    if seg_durations and sum(seg_durations) > 0:
        mean_dur = float(np.mean(seg_durations))
        std_dur = float(np.std(seg_durations))
        cv = std_dur / mean_dur if mean_dur > 0 else 0.0
    else:
        cv = 0.0

    # 4) Kelime içi pause tespiti — librosa.effects.split ile sessizlik aralıkları
    intervals = librosa.effects.split(audio, top_db=28)
    pauses_s: list[float] = []
    if len(intervals) > 1:
        for i in range(1, len(intervals)):
            gap_samples = intervals[i][0] - intervals[i - 1][1]
            gap_s = gap_samples / SAMPLE_RATE
            if gap_s >= 0.10:  # 100ms+ pause kayda değer
                pauses_s.append(round(gap_s, 3))
    # Choppy: hedef kısa metin (≤15 karakter, tek-iki kelime) ve 1+ pause var
    n_words = max(1, len(target_text.split()))
    is_choppy = len(pauses_s) >= n_words and any(p > 0.15 for p in pauses_s)

    # Eşikler — pratik aralık (eğitim hızı + normal konuşma kabul):
    #   < 4   çok yavaş / tutuk
    #   4-13  kabul edilebilir (eğitmen 5-7 ideal, normal konuşma 10-13)
    #   13-17 hızlı (yumuşak uyarı)
    #   > 17  çok hızlı (sert uyarı)
    # data/lexicon/pace_stats.json: eğitmenler 2.8-7.8 cps konuşur
    is_too_slow = speech_rate_cps < 4.0
    is_too_fast = speech_rate_cps > 17.0
    is_quite_fast = 13.0 < speech_rate_cps <= 17.0

    # 5) Praat (parselmouth) ile gelişmiş feature'lar
    praat = _praat_features(audio_path)
    hnr_db = praat["hnr_db"]
    intensity_range_db = praat["intensity_range_db"]
    # Praat'ın pitch dinamiğini librosa olanla en büyüğünü tut (daha duyarlı)
    f0_range_semitones = max(f0_range_semitones, praat.get("pitch_std_st", 0.0))
    is_monotonic = f0_range_semitones < 1.5  # yeniden hesapla
    is_breathy_or_noisy = 0.0 < hnr_db < 8.0   # düşük HNR = hırıltılı/sağlıksız ses
    has_flat_intensity = intensity_range_db > 0 and intensity_range_db < 6.0

    issues: list[str] = []
    if is_monotonic:
        issues.append(
            f"Sesin perdesi çok düz/monoton ({f0_range_semitones:.1f} semitone; "
            f"doğal 3-7). Cümle içinde hafif yükseliş/iniş yap, daha canlı söyle."
        )
    if has_flat_intensity:
        issues.append(
            f"Ses gücün hep aynı seviyede ({intensity_range_db:.1f} dB; doğal >8). "
            "Vurgulu hecelerde ses biraz yükselsin, gücü de oynat."
        )
    if is_too_slow:
        issues.append(
            f"Konuşman çok yavaş ({speech_rate_cps:.1f} karakter/saniye). "
            "Tutuk söylüyor olabilirsin; tek nefeste, akıcı söylemeye çalış."
        )
    if is_too_fast:
        issues.append(
            f"Konuşman çok hızlı ({speech_rate_cps:.1f} karakter/saniye; "
            f"eğitim hızı 5-7). Bu hızda sesler birbirine karışır, "
            "anlaşılırlık düşer. Yavaşla, her sesi net çıkar."
        )
    elif is_quite_fast:
        issues.append(
            f"Konuşman biraz hızlı ({speech_rate_cps:.1f} karakter/saniye; "
            f"eğitim hızı 5-7). Heceleri belirgin tutmak için biraz "
            "yavaşlayabilirsin."
        )
    if is_breathy_or_noisy:
        issues.append(
            f"Sesin biraz hırıltılı/titrek (HNR {hnr_db:.1f} dB; sağlıklı >12). "
            "Daha temiz, dolu bir ses çıkarmaya çalış; gerekirse mikrofon "
            "yakınlığını/oda gürültüsünü kontrol et."
        )
    if is_choppy and pauses_s:
        issues.append(
            f"Kelimeyi tek nefeste söylemiyorsun, hece hece bölüyorsun "
            f"(kelime içi {len(pauses_s)} duraklama). "
            "Heceleri birbirine bağla, akıcı söyle."
        )

    return NaturalnessReport(
        speech_rate_cps=round(speech_rate_cps, 2),
        f0_range_semitones=round(f0_range_semitones, 2),
        hnr_db=round(hnr_db, 2),
        intensity_range_db=round(intensity_range_db, 2),
        is_monotonic=is_monotonic,
        is_too_slow=is_too_slow,
        is_too_fast=is_too_fast,
        is_choppy=is_choppy,
        is_breathy_or_noisy=is_breathy_or_noisy,
        has_flat_intensity=has_flat_intensity,
        intra_word_pauses_s=pauses_s,
        syllable_duration_cv=round(cv, 3),
        issues=issues,
    )


@dataclasses.dataclass
class StressMeasurement:
    """Bir kelime için ölçülen ve beklenen vurgu yerleri."""
    word: str
    syllables: list[str]
    expected_stress_idx: int
    measured_stress_idx: int
    syllable_f0: list[float]    # her hecenin F0 ortalaması (Hz)
    syllable_energy: list[float]  # her hecenin enerji ortalaması (RMS)
    confident: bool             # ölçüm güvenilir mi (yeterli sesli hece var mı)
    word_start_s: float
    word_end_s: float

    @property
    def stress_correct(self) -> bool:
        return self.confident and self.measured_stress_idx == self.expected_stress_idx


def _words_from_char_segments(char_segments: list[CharSegment]) -> list[dict]:
    """Char segments'ten kelime sınırlarını çıkar ('|' karakterleri ayırıcı)."""
    words: list[dict] = []
    cur_chars: list[str] = []
    cur_start: float = 0.0
    cur_end: float = 0.0
    for seg in char_segments:
        if seg.char == "|":
            if cur_chars:
                words.append({
                    "word": "".join(cur_chars),
                    "start_s": cur_start,
                    "end_s": cur_end,
                })
                cur_chars = []
        else:
            if not cur_chars:
                cur_start = seg.start_s
            cur_chars.append(seg.target_char or seg.char)
            cur_end = seg.end_s
    if cur_chars:
        words.append({
            "word": "".join(cur_chars),
            "start_s": cur_start,
            "end_s": cur_end,
        })
    return words


def _syllable_boundaries(word: str, syllables: list[str]) -> list[tuple[int, int]]:
    """Her hece için (char_start_idx, char_end_idx) listesi (kelime içi)."""
    bounds: list[tuple[int, int]] = []
    cursor = 0
    for syll in syllables:
        bounds.append((cursor, cursor + len(syll)))
        cursor += len(syll)
    return bounds


def measure_word_stress(
    audio_path: Path,
    char_segments: list[CharSegment],
    target_text: str,
) -> list[StressMeasurement]:
    """Her kelime için ses üzerinde gerçek vurguyu ölç + beklenenle kıyasla.

    Yöntem:
      1. Char segments'ten kelime sınırları çıkar
      2. Her kelime için stress.syllabify ile hece böl
      3. Her hecenin (start_s, end_s) zamanlamasını char_segments'ten map'le
      4. F0 ve enerji ortalamalarını hesapla
      5. En yüksek (F0+enerji birleşik) skoru olan hece = ölçülen vurgu
      6. stress.stress_index ile beklenen vurgu yerini al
    """
    from stress import stress_index, syllabify  # circular import guard
    audio, _ = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    audio, _ = librosa.effects.trim(audio, top_db=30)
    f0 = _safe_f0(audio)
    rms = librosa.feature.rms(y=audio, hop_length=HOP_LENGTH)[0]

    word_segs = _words_from_char_segments(char_segments)
    target_words = target_text.split()
    measurements: list[StressMeasurement] = []

    for i, ws in enumerate(word_segs):
        # Orijinal kelimeyi al (target_words'tan; char segs noktalama içermeyebilir)
        if i < len(target_words):
            orig_word = target_words[i]
        else:
            orig_word = ws["word"]
        # Vurgu için temizle (noktalama at)
        import re
        clean_word = re.sub(r"[^\wçğışöü]", "", orig_word.lower())
        if not clean_word:
            continue
        sylls = syllabify(clean_word)
        if len(sylls) < 2:
            continue  # tek heceli kelime için vurgu kavramı yok

        bounds = _syllable_boundaries(clean_word, sylls)
        word_dur = ws["end_s"] - ws["start_s"]
        if word_dur <= 0 or len(clean_word) == 0:
            continue

        # Her karakterin oransal pozisyonu (char_segments'ten gerçek zamanları al)
        # Basit yaklaşım: kelime karakter sayısına orantılı süre dağılımı
        syll_f0: list[float] = []
        syll_energy: list[float] = []
        for cs, ce in bounds:
            t_start = ws["start_s"] + (cs / len(clean_word)) * word_dur
            t_end = ws["start_s"] + (ce / len(clean_word)) * word_dur
            f0_mean, energy = _segment_features(audio, f0, rms, t_start, t_end)
            syll_f0.append(f0_mean if np.isfinite(f0_mean) else 0.0)
            syll_energy.append(energy)

        # En az 2 hecede F0 olmalı (sesli)
        n_voiced = sum(1 for f in syll_f0 if f > 0)

        # Birleşik skor: F0 (normalize) + energy (normalize)
        f0_arr = np.array(syll_f0, dtype=float)
        en_arr = np.array(syll_energy, dtype=float)
        f0_norm = f0_arr / max(np.max(f0_arr), 1e-6) if np.max(f0_arr) > 0 else f0_arr
        en_norm = en_arr / max(np.max(en_arr), 1e-6) if np.max(en_arr) > 0 else en_arr
        combined = 0.55 * f0_norm + 0.45 * en_norm
        measured_idx = int(np.argmax(combined))

        # Confidence: hem sesli hece sayısı hem de peak'in netliği önemli.
        # Eğer en yüksek vs ikinci yüksek arasındaki fark çok düşükse,
        # sinyal belirsiz — yanlış pozitif vermemek için "güvensiz" işaretle.
        sorted_scores = np.sort(combined)[::-1]
        peak_margin = float(sorted_scores[0] - sorted_scores[1]) if len(sorted_scores) >= 2 else 0.0
        confident = (
            n_voiced >= max(2, len(sylls) // 2)
            and peak_margin >= 0.20  # net bir peak gerek (cümle bağlamı yanlış pozitiflerini ele)
        )

        expected_idx = stress_index(clean_word)
        if expected_idx < 0:
            expected_idx = len(sylls) - 1  # default: son hece

        measurements.append(StressMeasurement(
            word=orig_word,
            syllables=sylls,
            expected_stress_idx=expected_idx,
            measured_stress_idx=measured_idx,
            syllable_f0=[round(f, 1) for f in syll_f0],
            syllable_energy=[round(float(e), 4) for e in syll_energy],
            confident=confident,
            word_start_s=round(ws["start_s"], 3),
            word_end_s=round(ws["end_s"], 3),
        ))

    return measurements


def report(comp: ProsodyComparison) -> str:
    lines = [f"Genel sapma: {comp.overall_severity:.2f}  (0=esit, 1=cok farkli)"]
    if comp.biggest_outliers:
        lines.append("En buyuk sapmalar:")
        for d in comp.biggest_outliers:
            lines.append(
                f"  '{d.char}' @{d.user_start_s:5.2f}s  "
                f"sure x{d.duration_ratio:.2f}  "
                f"F0 x{d.f0_ratio:.2f}  "
                f"enerji x{d.energy_ratio:.2f}  "
                f"(sev {d.severity:.2f})"
            )
    return "\n".join(lines)
