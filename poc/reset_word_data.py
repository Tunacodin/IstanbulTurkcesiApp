"""Eski word_clips ve kelime-yt-* alistirmalarini temizle.
Yeni 17 Mennan Sahin video'sundan baslamak icin reset.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EX_PATH = REPO_ROOT / "data" / "exercises" / "exercises.json"
INDEX = REPO_ROOT / "data" / "knowledge" / "word_clips_index.json"
CLIPS_DIR = REPO_ROOT / "data" / "knowledge" / "word_clips"

# 1) exercises.json'dan kelime-yt-* sil
with open(EX_PATH, encoding="utf-8") as f:
    data = json.load(f)
before = len(data["exercises"])
data["exercises"] = [ex for ex in data["exercises"]
                     if not ex.get("id", "").startswith("kelime-yt-")]
after = len(data["exercises"])
with open(EX_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"exercises.json: {before} -> {after} ({before-after} kelime-yt-* silindi)")

# 2) word_clips_index.json sil
if INDEX.exists():
    INDEX.unlink()
    print(f"word_clips_index.json silindi")

# 3) word_clips/ icindeki .wav dosyalarini sil
removed = 0
if CLIPS_DIR.exists():
    for wav in CLIPS_DIR.glob("*.wav"):
        wav.unlink()
        removed += 1
print(f"word_clips/: {removed} wav silindi")

print("\nReset tamam. Build word_clips_index sonrasi yeni kelime havuzu hazir olacak.")
