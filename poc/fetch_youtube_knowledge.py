"""Verilen YouTube videolarinin metadata + transkriptini indirip
data/knowledge/youtube_transcripts/<video_id>.json olarak ariv eder.

Kullanim:
    python fetch_youtube_knowledge.py
        # config'deki tum URL'leri isler

Output her video icin:
{
  "url": "...",
  "video_id": "...",
  "title": "...",
  "channel": "...",
  "duration_s": 0,
  "license": "...",
  "transcript": [
    {"start": 0.0, "duration": 2.4, "text": "..."},
    ...
  ],
  "transcript_text": "...butun metin...",
  "downloaded_at": "..."
}

UYARI: Bu sadece transcript ve metadata cekiyor; ses dosyasi indirmiyor.
Telif acisindan en guvenli hareket. Ses kullanimi icin extract_reference_from_youtube
ve --require-cc + izinli icerik gerek.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "knowledge" / "youtube_transcripts"

# Mennan Sahin oynatma listesi (17 video) — MVP icin ana kaynak.
# Kanal ses kalitesi yuksek, spiker karakterli, standart Istanbul Turkcesi.
URLS = [
    "https://www.youtube.com/watch?v=aJazTUU3tXs",
    "https://www.youtube.com/watch?v=AddQUnG60fw",
    "https://www.youtube.com/watch?v=n0rUt1faf-Q",
    "https://www.youtube.com/watch?v=lzfOZqBuY28",
    "https://www.youtube.com/watch?v=0rkDTkoKAKw",
    "https://www.youtube.com/watch?v=egAl_MEjLqw",
    "https://www.youtube.com/watch?v=WbSeWUWovgo",
    "https://www.youtube.com/watch?v=wJLouPMZDKk",
    "https://www.youtube.com/watch?v=I_D1Wke9qqo",
    "https://www.youtube.com/watch?v=RE2WWWkiXpY",
    "https://www.youtube.com/watch?v=k4MJQ8yMkhM",
    "https://www.youtube.com/watch?v=ZhZYdSyaRpw",
    "https://www.youtube.com/watch?v=FEBh6xLkps4",
    "https://www.youtube.com/watch?v=IyPMXHXhY7Q",
    "https://www.youtube.com/watch?v=kxEwu4mOqRg",
    "https://www.youtube.com/watch?v=e5H5ejWKYYA",
    "https://www.youtube.com/watch?v=IE8RF5tlZrI",
]


def video_id_from_url(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|/shorts/)([\w-]{11})", url)
    if not m:
        raise ValueError(f"Geçersiz YT URL: {url}")
    return m.group(1)


def fetch_metadata(url: str) -> dict:
    """yt-dlp ile metadata cek (ses indirmez). Venv binary'sini kullan."""
    cmd = [sys.executable, "-m", "yt_dlp", "--dump-json", "--skip-download", url]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
    return json.loads(result.stdout.strip().splitlines()[0])


def fetch_transcript(video_id: str, languages: list[str] | None = None) -> list[dict]:
    """youtube-transcript-api ile TR (mumkunse) transkript cek.
    Yeni API: instance.fetch(video_id, languages=...).snippets"""
    from youtube_transcript_api import YouTubeTranscriptApi
    languages = languages or ["tr", "tr-TR", "en"]
    try:
        # Yeni 1.x API
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=languages)
        return [
            {"text": s.text, "start": s.start, "duration": s.duration}
            for s in fetched.snippets
        ]
    except AttributeError:
        # Eski API geriye dönük uyum
        try:
            return YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        except Exception as exc:
            print(f"  [!] Transkript çekilemedi: {exc}")
            return []
    except Exception as exc:
        print(f"  [!] Transkript çekilemedi: {exc}")
        return []


def fetch_one(url: str) -> dict | None:
    vid = video_id_from_url(url)
    print(f"\n→ {url}  (id={vid})")
    try:
        meta = fetch_metadata(url)
    except subprocess.CalledProcessError as exc:
        print(f"  [!] Metadata çekilemedi: {exc.stderr or exc}")
        return None
    title = meta.get("title", "?")
    channel = meta.get("channel") or meta.get("uploader", "?")
    duration = meta.get("duration")
    lic = meta.get("license") or "unknown"
    print(f"  başlık : {title}")
    print(f"  kanal  : {channel}")
    print(f"  süre   : {duration}s")
    print(f"  lisans : {lic}")

    tx = fetch_transcript(vid)
    print(f"  transcript: {len(tx)} segment")

    full_text = " ".join(seg["text"] for seg in tx).strip()
    record = {
        "url": url,
        "video_id": vid,
        "title": title,
        "channel": channel,
        "duration_s": duration,
        "license": lic,
        "transcript": tx,
        "transcript_text": full_text,
        "downloaded_at": dt.datetime.now().isoformat(),
        "note": "Sadece metin/metadata. Ses dosyası indirilmedi (telif önlemi).",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{vid}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"  yazıldı: {out_path}")
    return record


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = []
    for url in URLS:
        rec = fetch_one(url)
        if rec:
            summary.append({
                "video_id": rec["video_id"],
                "title": rec["title"],
                "transcript_segments": len(rec["transcript"]),
                "duration_s": rec["duration_s"],
                "license": rec["license"],
            })
    with open(OUT_DIR / "_index.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nÖzet: {len(summary)}/{len(URLS)} başarıyla indirildi.")
    print(f"İndex: {OUT_DIR/'_index.json'}")


if __name__ == "__main__":
    main()
