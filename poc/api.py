"""
FastAPI servis sarmali.

POST /assess
  multipart/form-data:
    audio: ses dosyasi (wav/mp3/...)
    target_text: hedef metin (string)
  donus: JSON {overall_score, verdict, target_text, segments, issues, feedback_text}

GET /exercises
  Mevcut alistirma havuzunu listele (data/exercises/exercises.json'dan).

GET /
  Healthcheck.

Calistirma:
  uvicorn api:app --reload --port 8000
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from typing import Optional

from fastapi.responses import FileResponse

from align_and_score import assess, assess_with_transcription
from feedback import make_feedback
from prosody import analyze_naturalness, compare, extract_prosody, measure_word_stress

REPO_ROOT = Path(__file__).resolve().parent.parent
EXERCISES_PATH = REPO_ROOT / "data" / "exercises" / "exercises.json"
REFS_DIR = REPO_ROOT / "data" / "exercises" / "refs"
WORD_CLIPS_INDEX = REPO_ROOT / "data" / "knowledge" / "word_clips_index.json"
WORD_CLIPS_DIR = REPO_ROOT / "data" / "knowledge" / "word_clips"

# .webmanifest dosyalarinin dogru MIME type ile sunulmasi icin
import mimetypes
mimetypes.add_type("application/manifest+json", ".webmanifest")

app = FastAPI(
    title="İstanbul Türkçesi Diksiyon API",
    description="Read-aloud pronunciation assessment for Standard Turkish.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # POC: same-origin static + her tarayıcıdan deneme için açık
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static recorder UI
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")


@app.get("/")
def health() -> dict:
    return {"status": "ok", "service": "istanbul-turkcesi-api"}


@app.get("/exercises")
def list_exercises() -> dict:
    if not EXERCISES_PATH.exists():
        raise HTTPException(404, f"Egzersiz dosyasi yok: {EXERCISES_PATH}")
    with open(EXERCISES_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.get("/reference/{exercise_id}")
def get_reference(exercise_id: str):
    """Belirtilen alıştırma için referans ses dosyası.
    Öncelik:
      1. exercises.json'da ref_source=='word_clip' ise word_clips'ten al
      2. Aksi takdirde data/exercises/refs/<id>.wav (TTS)
    """
    safe_id = "".join(c for c in exercise_id if c.isalnum() or c in "-_")

    # Alıştırmayı bul ve ref_source kontrol et
    if EXERCISES_PATH.exists():
        with open(EXERCISES_PATH, encoding="utf-8") as f:
            data = json.load(f)
        ex = next((e for e in data.get("exercises", []) if e.get("id") == safe_id), None)
        if ex and ex.get("ref_source") == "word_clip":
            key = _normalize_word_for_lookup(ex.get("text", ""))
            idx = _load_word_clips_index()
            occs = idx.get(key)
            if occs:
                clip_rel = occs[0].get("clip_path")
                if clip_rel:
                    wav = REPO_ROOT / clip_rel
                    if wav.exists():
                        return FileResponse(wav, media_type="audio/wav")

    wav = REFS_DIR / f"{safe_id}.wav"
    if not wav.exists():
        raise HTTPException(404, f"Referans yok: {exercise_id}")
    return FileResponse(wav, media_type="audio/wav")


def _normalize_word_for_lookup(w: str) -> str:
    """Kelime arama için: lowercase, noktalamaları at."""
    import re
    w = w.replace("I", "ı").replace("İ", "i").lower()
    return re.sub(r"[^\wçğışöü]", "", w)


_word_clips_cache: Optional[dict] = None


def _load_word_clips_index() -> dict:
    global _word_clips_cache
    if _word_clips_cache is None:
        if WORD_CLIPS_INDEX.exists():
            with open(WORD_CLIPS_INDEX, encoding="utf-8") as f:
                _word_clips_cache = json.load(f)
        else:
            _word_clips_cache = {}
    return _word_clips_cache


@app.get("/available-clips")
def available_clips() -> dict:
    """Hangi kelimeler için video kesiti var? UI'ya kelime listesi döndürür."""
    idx = _load_word_clips_index()
    return {"words": sorted(idx.keys()), "count": len(idx)}


@app.get("/videos-with-words")
def videos_with_words() -> dict:
    """Parse edilmiş diksiyon videolarını ve her birinin kelime listesini döndür.
    UI'da 'Video Sözlüğü' sekmesi için kullanılır."""
    tx_dir = REPO_ROOT / "data" / "knowledge" / "youtube_transcripts"
    idx = _load_word_clips_index()

    # Her kelimenin hangi video(lar)dan geldiğini map'le
    by_video: dict[str, list[dict]] = {}
    for word, occs in idx.items():
        for occ in occs[:1]:  # en iyi örneği al
            vid = occ.get("video_id")
            if not vid:
                continue
            if vid not in by_video:
                by_video[vid] = []
            by_video[vid].append({
                "word": word,
                "score": occ.get("score", 0),
                "duration_s": occ.get("duration_s", 0),
                "context": occ.get("context", ""),
            })

    # Video metadata'larını yükle
    videos = []
    if tx_dir.exists():
        for path in sorted(tx_dir.glob("*.json")):
            if path.name.startswith("_"):
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            vid = data.get("video_id")
            words = by_video.get(vid, [])
            words.sort(key=lambda w: -w["score"])
            videos.append({
                "video_id": vid,
                "title": data.get("title", ""),
                "channel": data.get("channel", ""),
                "duration_s": data.get("duration_s"),
                "url": data.get("url"),
                "word_count": len(words),
                "words": words,
            })
    return {"videos": videos}


@app.get("/word-clip/{word}")
def get_word_clip(word: str):
    """Belirtilen kelimenin diksiyon eğitmen videosundaki en iyi telaffuz örneği."""
    key = _normalize_word_for_lookup(word)
    idx = _load_word_clips_index()
    occs = idx.get(key)
    if not occs:
        raise HTTPException(404, f"Kelime için örnek yok: {word}")
    best = occs[0]
    clip_rel = best.get("clip_path")
    if not clip_rel:
        raise HTTPException(404, f"Kesit dosyası bulunamadı: {word}")
    # word_clips_index.json Windows'ta uretildigi icin backslash icerir; Linux container'da normalize et
    clip_rel = str(clip_rel).replace("\\", "/")
    wav = REPO_ROOT / clip_rel
    if not wav.exists():
        raise HTTPException(404, f"Kesit dosyası diskte yok: {wav}")
    return FileResponse(wav, media_type="audio/wav")


@app.get("/word-clip-info/{word}")
def get_word_clip_info(word: str) -> dict:
    """Kelime için varsa örnek meta bilgisi (kaynak video, bağlam, süre)."""
    key = _normalize_word_for_lookup(word)
    idx = _load_word_clips_index()
    occs = idx.get(key)
    if not occs:
        raise HTTPException(404, f"Kelime için örnek yok: {word}")
    return {"word": word, "occurrences": occs[:3]}


async def _save_upload(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await upload.read()
        tmp.write(content)
        return Path(tmp.name)


@app.post("/assess")
async def assess_endpoint(
    audio: UploadFile = File(..., description="Kullanici ses dosyasi"),
    target_text: str = Form(..., description="Hedef metin"),
    reference_audio: UploadFile | None = File(
        None, description="Egitmen referans sesi (opsiyonel; vurgu kıyasi icin)"
    ),
) -> dict:
    if not target_text.strip():
        raise HTTPException(400, "target_text bos olamaz")

    user_path = await _save_upload(audio)
    ref_path = await _save_upload(reference_audio) if reference_audio else None

    try:
        segments, transcription = assess_with_transcription(user_path, target_text)
        naturalness = analyze_naturalness(user_path, segments, target_text)
        stress_measurements = measure_word_stress(user_path, segments, target_text)
        prosody_comparison = None
        if ref_path is not None:
            ref_segments = assess(ref_path, target_text)
            user_pros = extract_prosody(user_path, segments)
            ref_pros = extract_prosody(ref_path, ref_segments)
            prosody_comparison = compare(user_pros, ref_pros)
    except Exception as exc:
        raise HTTPException(500, f"Pipeline hatasi: {exc}")
    finally:
        user_path.unlink(missing_ok=True)
        if ref_path is not None:
            ref_path.unlink(missing_ok=True)

    fb = make_feedback(
        segments, target_text,
        prosody=prosody_comparison,
        transcription=transcription,
        naturalness=naturalness,
        stress_measurements=stress_measurements,
    )
    result = fb.to_dict()
    result["segments"] = [
        {
            "char": s.char,
            "start_s": round(s.start_s, 3),
            "end_s": round(s.end_s, 3),
            "score": round(s.score, 3),
        }
        for s in segments
    ]
    if prosody_comparison is not None:
        result["prosody"] = {
            "overall_severity": prosody_comparison.overall_severity,
            "biggest_outliers": [
                {
                    "char": d.char,
                    "user_start_s": round(d.user_start_s, 3),
                    "duration_ratio": d.duration_ratio,
                    "f0_ratio": d.f0_ratio,
                    "energy_ratio": d.energy_ratio,
                    "severity": d.severity,
                }
                for d in prosody_comparison.biggest_outliers
            ],
        }
    return result
