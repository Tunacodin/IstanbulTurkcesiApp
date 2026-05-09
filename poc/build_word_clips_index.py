"""4 diksiyon videosundan kelime bazli telaffuz kutuphanesi olustur.

Adimlar:
  1. Her video transkriptindeki ifadeyi audio'dan kes (start, end)
  2. Wav2Vec2 forced alignment ile kelime sinirlarini cikar
  3. Word-level index olustur: {kelime: [(video_id, start_s, end_s, baglam), ...]}

Cikti:
  data/knowledge/word_clips_index.json
  data/knowledge/word_clips/<word>__<video_id>__<start>.wav  (her kelime icin kisa kesit)

Not: Buyuk i%351, ilk koşturmada birkaç dakika sürer.
"""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf

from align_and_score import _get_model_and_processor, build_trellis, backtrack, normalize_text_for_ctc, get_emissions, _last_non_blank_frame

REPO_ROOT = Path(__file__).resolve().parent.parent
TX_DIR = REPO_ROOT / "data" / "knowledge" / "youtube_transcripts"
AUDIO_DIR = REPO_ROOT / "data" / "knowledge" / "youtube_audio"
CLIPS_DIR = REPO_ROOT / "data" / "knowledge" / "word_clips"
INDEX_PATH = REPO_ROOT / "data" / "knowledge" / "word_clips_index.json"

SAMPLE_RATE = 16_000
PAD_S = 0.05  # kelime kesit etrafına biraz tampon


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:40] or "x"


def normalize_word(w: str) -> str:
    """noktalama at, küçük harfe çevir."""
    w = w.replace("I", "ı").replace("İ", "i").lower()
    w = re.sub(r"[^\wçğışöü]", "", w)
    return w


_full_audio_cache: dict[Path, np.ndarray] = {}


def load_full_audio(path: Path) -> np.ndarray:
    """Tüm wav dosyasını bir kere yükle, cache'le."""
    if path in _full_audio_cache:
        return _full_audio_cache[path]
    import librosa
    audio, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    _full_audio_cache[path] = audio
    return audio


def load_audio(path: Path, start_s: float, end_s: float) -> np.ndarray:
    """Audio'nun belirli bir kesitini cache'lenmis wav'dan numpy slicing ile al."""
    full = load_full_audio(path)
    s_idx = max(0, int(start_s * SAMPLE_RATE))
    e_idx = min(len(full), int(end_s * SAMPLE_RATE))
    if e_idx <= s_idx:
        return np.array([], dtype=np.float32)
    return full[s_idx:e_idx]


def align_segment(audio: np.ndarray, target_text: str) -> tuple[list[dict], float]:
    """Bir ses parçasını target metne hizala. Karakter seviyesi segmentler döner."""
    import torch
    model, processor = _get_model_and_processor()
    inputs = processor(audio, sampling_rate=SAMPLE_RATE, return_tensors="pt")
    with torch.no_grad():
        logits = model(inputs.input_values).logits[0]
    emission = torch.log_softmax(logits, dim=-1)
    vocab = processor.tokenizer.get_vocab()
    target, target_orig = normalize_text_for_ctc(target_text, vocab)
    if not target:
        return [], 0.0
    tokens = [vocab[c] for c in target]
    blank_id = vocab.get("<pad>", 0)
    trellis = build_trellis(emission, tokens, blank_id)
    transitions = backtrack(trellis, emission, tokens, blank_id)
    if not transitions:
        return [], 0.0
    end_frame = _last_non_blank_frame(emission, blank_id)
    frame_duration_s = len(audio) / SAMPLE_RATE / emission.size(0)
    transitions_sorted = sorted(transitions, key=lambda x: x[1])
    out: list[dict] = []
    for i, (t_idx, tok_idx, log_prob) in enumerate(transitions_sorted):
        next_t = transitions_sorted[i + 1][0] if i + 1 < len(transitions_sorted) else end_frame
        out.append({
            "char": target[tok_idx],
            "orig_char": target_orig[tok_idx] if tok_idx < len(target_orig) else target[tok_idx],
            "start_s": t_idx * frame_duration_s,
            "end_s": next_t * frame_duration_s,
            "score": float(np.exp(log_prob)),
        })
    return out, frame_duration_s


def words_from_chars(char_segs: list[dict]) -> list[dict]:
    """Karakter segmentlerini '|' (boşluk) bölüm noktasıyla kelimelere ayır."""
    words: list[dict] = []
    cur: list[dict] = []
    for seg in char_segs:
        if seg["char"] == "|":
            if cur:
                words.append({
                    "word": "".join(s["orig_char"] for s in cur),
                    "start_s": cur[0]["start_s"],
                    "end_s": cur[-1]["end_s"],
                    "avg_score": float(np.mean([s["score"] for s in cur])),
                })
                cur = []
        else:
            cur.append(seg)
    if cur:
        words.append({
            "word": "".join(s["orig_char"] for s in cur),
            "start_s": cur[0]["start_s"],
            "end_s": cur[-1]["end_s"],
            "avg_score": float(np.mean([s["score"] for s in cur])),
        })
    return words


def cut_audio(audio: np.ndarray, start_s: float, end_s: float, out_path: Path) -> None:
    s_idx = max(0, int((start_s - PAD_S) * SAMPLE_RATE))
    e_idx = min(len(audio), int((end_s + PAD_S) * SAMPLE_RATE))
    if e_idx <= s_idx:
        return
    sf.write(out_path, audio[s_idx:e_idx], SAMPLE_RATE)


def process_video(video_id: str) -> dict:
    tx_path = TX_DIR / f"{video_id}.json"
    audio_path = AUDIO_DIR / f"{video_id}.wav"
    if not audio_path.exists():
        print(f"  [{video_id}] ses dosyası yok, atlandı")
        return {}
    with open(tx_path, encoding="utf-8") as f:
        data = json.load(f)
    transcript = data.get("transcript", [])
    print(f"  [{video_id}] ses dosyası yükleniyor...", flush=True)
    load_full_audio(audio_path)
    print(f"  [{video_id}] {len(transcript)} segment hizalanıyor", flush=True)

    word_index: dict[str, list[dict]] = defaultdict(list)
    for i, seg in enumerate(transcript):
        if i > 0 and i % 25 == 0:
            print(f"    {i}/{len(transcript)} segment, "
                  f"{sum(len(v) for v in word_index.values())} kelime örneği bulundu",
                  flush=True)
        text = seg.get("text", "").strip()
        start = float(seg.get("start", 0.0))
        duration = float(seg.get("duration", 0.0))
        if not text or duration < 0.5 or duration > 8.0:
            continue
        try:
            audio_seg = load_audio(audio_path, start, start + duration)
            if audio_seg.size < SAMPLE_RATE * 0.3:  # 0.3 saniyeden kısa atla
                continue
            char_segs, _ = align_segment(audio_seg, text)
            words = words_from_chars(char_segs)
            for w in words:
                key = normalize_word(w["word"])
                if not key or len(key) < 2:
                    continue
                # Kelime süresi mantıksızsa atla
                wdur = w["end_s"] - w["start_s"]
                if wdur < 0.10 or wdur > 1.5:
                    continue
                word_index[key].append({
                    "video_id": video_id,
                    "start_s": round(start + w["start_s"], 3),
                    "end_s": round(start + w["end_s"], 3),
                    "duration_s": round(wdur, 3),
                    "score": round(w["avg_score"], 3),
                    "context": text,
                })
        except Exception as exc:
            print(f"    seg {i} hata: {exc}")
            continue
    return dict(word_index)


def merge_indices(per_video: list[dict]) -> dict:
    merged: dict[str, list[dict]] = defaultdict(list)
    for d in per_video:
        for k, occs in d.items():
            merged[k].extend(occs)
    # Her kelime için skor sırasıyla en iyi 5 örneği tut
    out: dict[str, list[dict]] = {}
    for k, occs in merged.items():
        occs_sorted = sorted(occs, key=lambda o: -o["score"])[:5]
        out[k] = occs_sorted
    return out


def export_clips(index: dict) -> None:
    """Her kelimenin EN İYİ örneğini ayrı bir wav dosyası olarak yaz."""
    import librosa
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    audio_cache: dict[str, np.ndarray] = {}
    written = 0
    for word, occs in index.items():
        if not occs:
            continue
        best = occs[0]
        vid = best["video_id"]
        if vid not in audio_cache:
            audio_path = AUDIO_DIR / f"{vid}.wav"
            audio_cache[vid], _ = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
        audio = audio_cache[vid]
        slug = slugify(word)
        out_path = CLIPS_DIR / f"{slug}__{vid}__{best['start_s']:.2f}.wav"
        cut_audio(audio, best["start_s"], best["end_s"], out_path)
        # En iyi kesitin path'ini occs[0]'a yaz
        best["clip_path"] = str(out_path.relative_to(REPO_ROOT))
        written += 1
    print(f"  {written} kelime kesiti yazıldı → {CLIPS_DIR}")


def main() -> None:
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    print("Kelime bazlı telaffuz kütüphanesi oluşturuluyor...")
    print("(Wav2Vec2 forced alignment, ilk koşuda 5-10 dakika sürebilir)\n")
    per_video = []
    for path in TX_DIR.glob("*.json"):
        if path.name.startswith("_"):
            continue
        vid = path.stem
        d = process_video(vid)
        per_video.append(d)
        print(f"    -> {len(d)} farklı kelime")

    index = merge_indices(per_video)
    print(f"\nToplam farklı kelime: {len(index)}")
    print("Kelime kesitleri yazılıyor...")
    export_clips(index)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"\nİndeks: {INDEX_PATH}")


if __name__ == "__main__":
    main()
