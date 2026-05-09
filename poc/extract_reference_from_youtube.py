"""
YouTube referans ses çıkarma aracı (POC).

Bir YT URL'si ve hedef ifade listesi alır:
  1. Sesi indirir (yt-dlp, 16 kHz mono wav).
  2. Transcript'i çeker (youtube-transcript-api, TR).
  3. Hedef ifadeleri transcript'te bulur (kaba zaman damgası).
  4. Wav2Vec2 CTC forced alignment ile kelime seviyesinde rafine eder.
  5. Kesilmiş wav + metadata json'unu data/reference_audio/ altına yazar.

UYARI: Bu aracı sadece içerik sahibinin izinli/CC lisanslı içeriğinde koşturun.
YouTube ToS'u izinsiz indirmeyi yasaklamaktadır.

Kullanım:
    python extract_reference_from_youtube.py \
        --url "https://www.youtube.com/watch?v=XXXX" \
        --targets "merhaba" "hâlâ" "şu köşe yaz köşesi"

Bağımlılıklar:
    pip install yt-dlp youtube-transcript-api
    + poc/requirements.txt
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DIR = REPO_ROOT / "data" / "reference_audio"
SAMPLE_RATE = 16_000


@dataclass
class TranscriptHit:
    target: str
    transcript_text: str
    start_s: float
    end_s: float


@dataclass
class ReferenceClip:
    target: str
    source_url: str
    source_video_id: str
    start_s: float
    end_s: float
    duration_s: float
    output_path: str
    note: str = ""


def normalize(text: str) -> str:
    """Türkçe için case-insensitive eşleşme — diakritikleri koru."""
    text = text.lower()
    text = re.sub(r"[^\w\sÀ-ſğışçöü]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def video_id_from_url(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/|/shorts/)([\w-]{11})", url)
    if not match:
        raise ValueError(f"Geçerli bir YouTube video ID'si bulunamadı: {url}")
    return match.group(1)


def check_license(url: str) -> str:
    """Videonun lisansını yt-dlp ile çek; CC değilse kullanıcıyı uyar."""
    cmd = ["yt-dlp", "--dump-json", "--skip-download", url]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    data = json.loads(result.stdout.strip().splitlines()[0])
    return data.get("license") or "unknown"


def download_audio(url: str, out_dir: Path) -> Path:
    """yt-dlp ile en iyi ses parçasını indirip 16 kHz mono wav'a çevirir."""
    out_template = str(out_dir / "%(id)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--postprocessor-args", f"-ar {SAMPLE_RATE} -ac 1",
        "-o", out_template,
        url,
    ]
    subprocess.run(cmd, check=True)
    candidates = list(out_dir.glob("*.wav"))
    if not candidates:
        raise RuntimeError("yt-dlp bir wav dosyası üretmedi.")
    return candidates[0]


def fetch_transcript(video_id: str) -> list[dict]:
    """youtube-transcript-api ile TR transcript çek."""
    from youtube_transcript_api import YouTubeTranscriptApi
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=["tr"])
    except Exception as exc:
        raise RuntimeError(
            f"Transcript çekilemedi (video: {video_id}). "
            "Belki manuel/otomatik altyazı yok ya da bölge engeli var."
        ) from exc


def find_targets_in_transcript(
    transcript: list[dict], targets: list[str]
) -> list[TranscriptHit]:
    """Hedef ifadeyi transcript ifadelerinde substring olarak ara."""
    hits: list[TranscriptHit] = []
    for entry in transcript:
        text_norm = normalize(entry["text"])
        for target in targets:
            if normalize(target) in text_norm:
                hits.append(
                    TranscriptHit(
                        target=target,
                        transcript_text=entry["text"],
                        start_s=float(entry["start"]),
                        end_s=float(entry["start"]) + float(entry["duration"]),
                    )
                )
    return hits


def cut_segment(audio_path: Path, start_s: float, end_s: float, out_path: Path) -> None:
    """ffmpeg ile ses kesiti çıkar."""
    pad = 0.2
    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_path),
        "-ss", f"{max(0.0, start_s - pad):.3f}",
        "-to", f"{end_s + pad:.3f}",
        "-ar", str(SAMPLE_RATE), "-ac", "1",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def refine_with_alignment(clip_path: Path, target_text: str) -> tuple[float, float]:
    """
    Kaba kesit içinde target metnin gerçek başlangıç/bitişini bul.
    Wav2Vec2 forced alignment kullanır (align_and_score modülünden).
    """
    from align_and_score import assess
    segments = assess(clip_path, target_text)
    if not segments:
        return 0.0, 0.0
    real_start = segments[0].start_s
    real_end = segments[-1].end_s
    return real_start, real_end


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s_]+", "_", text)[:40]


def process(url: str, targets: list[str], dry_run: bool, require_cc: bool) -> list[ReferenceClip]:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    video_id = video_id_from_url(url)

    if require_cc:
        license_str = check_license(url)
        print(f"Video lisansı: {license_str}")
        if "creative_commons" not in license_str.lower() and "cc" not in license_str.lower():
            raise SystemExit(
                f"Bu video CC değil ('{license_str}'). --require-cc aktifken "
                "indirme yapılmaz. Manuel izin alındıysa --require-cc'yi kaldırın."
            )

    transcript = fetch_transcript(video_id)
    hits = find_targets_in_transcript(transcript, targets)

    if not hits:
        print("Hedef ifadelerden hiçbiri transcript'te bulunamadı.")
        return []

    print(f"{len(hits)} eşleşme bulundu:")
    for hit in hits:
        print(f"  [{hit.start_s:6.1f}-{hit.end_s:6.1f}] '{hit.target}' "
              f"  ←  '{hit.transcript_text[:60]}'")

    if dry_run:
        print("\n[dry-run] Ses indirilmedi.")
        return []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        full_audio = download_audio(url, tmp_path)

        clips: list[ReferenceClip] = []
        for i, hit in enumerate(hits):
            slug = slugify(hit.target)
            out_path = REFERENCE_DIR / f"{video_id}_{i:03d}_{slug}.wav"
            cut_segment(full_audio, hit.start_s, hit.end_s, out_path)
            try:
                start_offset, end_offset = refine_with_alignment(out_path, hit.target)
                refined_start = hit.start_s + start_offset - 0.2
                refined_end = hit.start_s + end_offset - 0.2
                cut_segment(full_audio, refined_start, refined_end, out_path)
                note = "alignment_refined"
            except Exception as exc:
                note = f"alignment_failed: {exc}"
                refined_start, refined_end = hit.start_s, hit.end_s

            clips.append(
                ReferenceClip(
                    target=hit.target,
                    source_url=url,
                    source_video_id=video_id,
                    start_s=refined_start,
                    end_s=refined_end,
                    duration_s=refined_end - refined_start,
                    output_path=str(out_path.relative_to(REPO_ROOT)),
                    note=note,
                )
            )

        meta_path = REFERENCE_DIR / f"{video_id}_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in clips], f, ensure_ascii=False, indent=2)
        print(f"\n{len(clips)} referans kesit yazıldı → {REFERENCE_DIR}")
        return clips


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--targets", nargs="+", required=True,
                        help="Aranan kelime/ifadeler (boşlukla ayrılmış)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Sadece transcript eşleşmelerini göster, ses indirme")
    parser.add_argument("--require-cc", action="store_true",
                        help="Sadece Creative Commons lisanslı videoları indir")
    args = parser.parse_args()

    if not shutil.which("yt-dlp") and not args.dry_run:
        print("UYARI: yt-dlp PATH'te bulunamadı. `pip install yt-dlp` ya da "
              "https://github.com/yt-dlp/yt-dlp adresinden kurun.")
    if not shutil.which("ffmpeg") and not args.dry_run:
        print("UYARI: ffmpeg PATH'te bulunamadı. ffmpeg sistem üzerine kurulu olmalı.")

    process(args.url, args.targets, args.dry_run, args.require_cc)


if __name__ == "__main__":
    main()
