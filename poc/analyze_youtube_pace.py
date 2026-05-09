"""YT diksiyon videolarinin transkript zaman damgalarindan
'gercek egitmen hizi' istatistiklerini cikar.

Cikti: data/lexicon/pace_stats.json
  {
    "median_cps": ..., "p5_cps": ..., "p95_cps": ...,
    "median_wps": ..., ...
  }
Yeni eşiklerimiz bu sayılara dayanır.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
TX_DIR = REPO_ROOT / "data" / "knowledge" / "youtube_transcripts"
OUT = REPO_ROOT / "data" / "lexicon" / "pace_stats.json"

# Çok kısa ve çok uzun segmentleri at — outlier filtresi
MIN_DUR_S = 1.0
MAX_DUR_S = 6.0
MIN_CHARS = 10


def main() -> None:
    cps_values: list[float] = []
    wps_values: list[float] = []
    seg_durations: list[float] = []
    word_counts: list[int] = []
    n_total = 0
    n_kept = 0

    for path in TX_DIR.glob("*.json"):
        if path.name.startswith("_"):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for seg in data.get("transcript", []):
            n_total += 1
            text = seg.get("text", "").strip()
            duration = float(seg.get("duration", 0.0))
            if duration < MIN_DUR_S or duration > MAX_DUR_S:
                continue
            n_chars = sum(1 for c in text if c.isalpha())
            words = text.split()
            if n_chars < MIN_CHARS:
                continue
            n_kept += 1
            cps_values.append(n_chars / duration)
            wps_values.append(len(words) / duration)
            seg_durations.append(duration)
            word_counts.append(len(words))

    if not cps_values:
        print("Hicbir veri yok.")
        return

    cps_arr = np.array(cps_values)
    wps_arr = np.array(wps_values)

    stats = {
        "kaynak": "Diksiyon Dersleri YT kanalı, 4 video transkripti",
        "toplam_segment": n_total,
        "filtrelenmis_segment": n_kept,
        "min_dur_s": MIN_DUR_S,
        "max_dur_s": MAX_DUR_S,
        "min_chars": MIN_CHARS,
        "cps": {
            "p5": round(float(np.percentile(cps_arr, 5)), 2),
            "p25": round(float(np.percentile(cps_arr, 25)), 2),
            "median": round(float(np.median(cps_arr)), 2),
            "p75": round(float(np.percentile(cps_arr, 75)), 2),
            "p95": round(float(np.percentile(cps_arr, 95)), 2),
            "mean": round(float(np.mean(cps_arr)), 2),
            "std": round(float(np.std(cps_arr)), 2),
        },
        "wps": {
            "p5": round(float(np.percentile(wps_arr, 5)), 2),
            "median": round(float(np.median(wps_arr)), 2),
            "p95": round(float(np.percentile(wps_arr, 95)), 2),
        },
        "onerilen_esikler": {
            "_aciklama": "Bu istatistiklere dayanarak naturalness modulundeki eşikler",
            "yavas_alt_siniri_cps": round(float(np.percentile(cps_arr, 5)), 1),
            "hizli_ust_siniri_cps": round(float(np.percentile(cps_arr, 95)), 1),
            "ideal_aralik_cps": [
                round(float(np.percentile(cps_arr, 25)), 1),
                round(float(np.percentile(cps_arr, 75)), 1),
            ],
        },
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"Toplam segment: {n_total}, filtreli kullanılan: {n_kept}")
    print(f"\nCPS dağılımı (karakter/saniye):")
    print(f"  P5  (yavaş sınır)  : {stats['cps']['p5']}")
    print(f"  P25                : {stats['cps']['p25']}")
    print(f"  Medyan             : {stats['cps']['median']}")
    print(f"  P75                : {stats['cps']['p75']}")
    print(f"  P95 (hızlı sınır)  : {stats['cps']['p95']}")
    print(f"  Ortalama ± std     : {stats['cps']['mean']} ± {stats['cps']['std']}")
    print(f"\nÖnerilen eşikler:")
    print(f"  Yavaş         : < {stats['onerilen_esikler']['yavas_alt_siniri_cps']} cps")
    print(f"  Hızlı         : > {stats['onerilen_esikler']['hizli_ust_siniri_cps']} cps")
    print(f"  Doğal aralık  : {stats['onerilen_esikler']['ideal_aralik_cps']}")
    print(f"\nKaydedildi: {OUT}")


if __name__ == "__main__":
    main()
