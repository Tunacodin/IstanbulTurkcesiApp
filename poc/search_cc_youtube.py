"""
YouTube'da Creative Commons lisanslı video arama yardımcısı.

YouTube'un public arama URL'sinde CC filtresi şu parametreyle:
    sp=EgIwAQ%3D%3D   (License: Creative Commons)

Bu script verilen sorguyla CC-filtreli aramayı yapıp video URL'lerini döner.
yt-dlp --flat-playlist ile sadece metadata çekilir, ses inmez.

Kullanım:
    python search_cc_youtube.py --query "istanbul türkçesi diksiyon" --max 20

Önemli:
- YouTube'un "CC" işaretlemesi her zaman doğru değildir; mutlaka video
  açıklamasından lisansı doğrulayın.
- "Standard YouTube License" olan içerikler yasal olarak indirilemez.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from urllib.parse import quote


def search(query: str, max_results: int) -> list[dict]:
    if not shutil.which("yt-dlp"):
        sys.exit("yt-dlp PATH'te yok. `pip install yt-dlp` ile kurun.")

    search_url = (
        f"https://www.youtube.com/results?"
        f"search_query={quote(query)}&sp=EgIwAQ%253D%253D"
    )
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--playlist-end", str(max_results),
        search_url,
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    videos = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            videos.append({
                "id": data.get("id"),
                "title": data.get("title"),
                "url": data.get("url") or f"https://www.youtube.com/watch?v={data.get('id')}",
                "duration_s": data.get("duration"),
                "channel": data.get("channel") or data.get("uploader"),
            })
        except json.JSONDecodeError:
            continue
    return videos


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--max", type=int, default=20)
    args = parser.parse_args()

    videos = search(args.query, args.max)
    print(f"\n{len(videos)} CC-aday video bulundu.\n")
    for v in videos:
        dur = f"{v['duration_s']/60:5.1f} dk" if v["duration_s"] else "  ?"
        print(f"  {dur}  {v['channel'][:25]:25s}  {v['title'][:60]}")
        print(f"         {v['url']}")
    print("\nNot: Lisansı YT video sayfasında 'Show more' altındaki bölümden")
    print("manuel olarak doğrulayın. CC işaretlemesi bazen yanlış olabiliyor.")


if __name__ == "__main__":
    main()
