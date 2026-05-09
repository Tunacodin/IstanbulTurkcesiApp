"""
Read-aloud pronunciation assessment POC.

Bilinen hedef metin + kullanıcı sesi → fonem-bazlı hizalama + skor.

Kullanım:
    python align_and_score.py --audio sample.wav --text "merhaba dünya"

Notlar:
- Türkçe wav2vec2 CTC modeli kullanılıyor.
- Forced alignment: HuggingFace'in "Forced Alignment with Wav2Vec2"
  tutorial'ındaki trellis yöntemi.
- Skor = ortalama log-probability, sigmoid'le 0-1'e normalize.
"""

from __future__ import annotations

import argparse
import dataclasses
from pathlib import Path

import librosa
import numpy as np
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

MODEL_ID = "mpoyraz/wav2vec2-xls-r-300m-cv8-turkish"
SAMPLE_RATE = 16_000
SCORE_THRESHOLD = 0.55  # ampirik; gerçek değer kullanıcı testinden gelmeli


@dataclasses.dataclass
class CharSegment:
    char: str            # alignment'ta kullanılan char (vocab'taki)
    start_s: float
    end_s: float
    score: float
    target_char: str = ""  # orijinal target_text karakter (â/î/û ayrımı için)

    @property
    def ok(self) -> bool:
        return self.score >= SCORE_THRESHOLD


def load_audio(path: Path) -> np.ndarray:
    audio, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    # Bastaki ve sondaki sessizligi kes — alignment'in sessizlige yamanmasini onler
    audio, _ = librosa.effects.trim(audio, top_db=30)
    return audio


def get_emissions(audio: np.ndarray, model, processor) -> tuple[torch.Tensor, dict]:
    inputs = processor(audio, sampling_rate=SAMPLE_RATE, return_tensors="pt")
    with torch.no_grad():
        logits = model(inputs.input_values).logits[0]
    log_probs = torch.log_softmax(logits, dim=-1)
    vocab = processor.tokenizer.get_vocab()
    return log_probs, vocab


def build_trellis(emission: torch.Tensor, tokens: list[int], blank_id: int) -> torch.Tensor:
    """Standart CTC forced-alignment trellis."""
    num_frames, _ = emission.shape
    num_tokens = len(tokens)
    trellis = torch.full((num_frames + 1, num_tokens + 1), -float("inf"))
    trellis[0, 0] = 0.0
    for t in range(num_frames):
        trellis[t + 1, 0] = trellis[t, 0] + emission[t, blank_id]
        for j in range(1, num_tokens + 1):
            stay = trellis[t, j] + emission[t, blank_id]
            change = trellis[t, j - 1] + emission[t, tokens[j - 1]]
            trellis[t + 1, j] = max(stay, change)
    return trellis


def backtrack(trellis: torch.Tensor, emission: torch.Tensor, tokens: list[int], blank_id: int):
    """Trellis üzerinden geri yürü, her token için *transition frame*'i bul.
    Her token'a tek bir (transition_frame, token_idx, log_prob) tuple'ı atanır.
    Token süreleri merge_to_chars'ta ardışık transition'lardan hesaplanır."""
    t, j = trellis.size(0) - 1, trellis.size(1) - 1
    transitions: list[tuple[int, int, float]] = []
    while j > 0 and t > 0:
        stayed = trellis[t - 1, j] + emission[t - 1, blank_id]
        changed = trellis[t - 1, j - 1] + emission[t - 1, tokens[j - 1]]
        if changed > stayed:
            transitions.append((t - 1, j - 1, emission[t - 1, tokens[j - 1]].item()))
            j -= 1
        t -= 1
    transitions.reverse()
    return transitions


def merge_to_chars(
    transitions, target_chars: str, frame_duration_s: float,
    target_chars_original: str = "", total_frames: int | None = None,
) -> list[CharSegment]:
    """Transition'lardan token segmentleri kur.
    Her token'ın start_frame'i kendi transition'ı, end_frame'i bir sonraki token'ın
    transition'ından bir önceki frame (son token için emission'ın son frame'i)."""
    segments: list[CharSegment] = []
    transitions_sorted = sorted(transitions, key=lambda x: x[1])
    n = len(transitions_sorted)
    for i, (t_start, token_idx, log_prob) in enumerate(transitions_sorted):
        next_t = (
            transitions_sorted[i + 1][0]
            if i + 1 < n else (total_frames or t_start + 1)
        )
        score = float(np.exp(log_prob))
        char = target_chars[token_idx]
        target_char = (
            target_chars_original[token_idx]
            if token_idx < len(target_chars_original) else char
        )
        segments.append(
            CharSegment(
                char=char,
                start_s=t_start * frame_duration_s,
                end_s=next_t * frame_duration_s,
                score=score,
                target_char=target_char,
            )
        )
    return segments


_LONG_TO_PLAIN = {"â": "a", "î": "i", "û": "u"}


def normalize_text_for_ctc(text: str, vocab: dict) -> tuple[str, str]:
    """
    Hedefi vocab'a uyarla.
    Doner: (normalized, original)  - aynı uzunlukta; original karakterler korunur.
    â/î/û vocab'da yoksa a/i/u'ya fallback yapılır ama original'da işaretli kalır.
    """
    from g2p import tr_lower
    text = tr_lower(text).replace(" ", "|")
    norm_chars: list[str] = []
    orig_chars: list[str] = []
    for c in text:
        if c in vocab:
            norm_chars.append(c)
            orig_chars.append(c)
            continue
        # â/î/û fallback
        plain = _LONG_TO_PLAIN.get(c)
        if plain and plain in vocab:
            norm_chars.append(plain)
            orig_chars.append(c)  # uzun işaret korundu
    return "".join(norm_chars), "".join(orig_chars)


_processor = None
_model = None


def _get_model_and_processor():
    """Model ve processor'i tek sefer yukle (singleton)."""
    global _processor, _model
    if _processor is None:
        # Wav2Vec2Processor (LM'siz) kullaniyoruz; forced alignment icin LM gerekmez.
        _processor = Wav2Vec2Processor.from_pretrained(MODEL_ID)
        _model = Wav2Vec2ForCTC.from_pretrained(MODEL_ID).eval()
    return _model, _processor


def greedy_transcribe(emission: torch.Tensor, vocab: dict) -> str:
    """CTC argmax + collapse blank/duplicate. Modelin 'duyduğu' metin."""
    blank_id = vocab.get("<pad>", 0)
    inv_vocab = {v: k for k, v in vocab.items()}
    indices = emission.argmax(dim=-1).tolist()
    out: list[str] = []
    prev = -1
    for idx in indices:
        if idx == blank_id:
            prev = idx
            continue
        if idx == prev:
            continue
        prev = idx
        ch = inv_vocab.get(idx, "")
        out.append(ch)
    return "".join(out).replace("|", " ").strip()


def transcribe(audio_path: Path) -> str:
    """Hedef metin olmadan, modelin sesi ne anladigini dondur."""
    model, processor = _get_model_and_processor()
    audio = load_audio(audio_path)
    emission, vocab = get_emissions(audio, model, processor)
    return greedy_transcribe(emission, vocab)


def _last_non_blank_frame(emission: torch.Tensor, blank_id: int) -> int:
    """Emission'da blank olmayan son frame indexi. Sessizlik son token'a yamanmasin."""
    argmax = emission.argmax(dim=-1)
    for i in range(emission.size(0) - 1, -1, -1):
        if int(argmax[i].item()) != blank_id:
            return i + 1  # exclusive end
    return emission.size(0)


def assess(audio_path: Path, target_text: str) -> list[CharSegment]:
    model, processor = _get_model_and_processor()

    audio = load_audio(audio_path)
    emission, vocab = get_emissions(audio, model, processor)

    target, target_orig = normalize_text_for_ctc(target_text, vocab)
    if not target:
        raise ValueError("Hedef metin model sözlüğüyle uyumsuz.")
    tokens = [vocab[c] for c in target]
    blank_id = vocab.get("<pad>", 0)

    trellis = build_trellis(emission, tokens, blank_id)
    path = backtrack(trellis, emission, tokens, blank_id)

    frame_duration_s = len(audio) / SAMPLE_RATE / emission.size(0)
    end_frame = _last_non_blank_frame(emission, blank_id)
    return merge_to_chars(path, target, frame_duration_s, target_orig, end_frame)


def assess_with_transcription(audio_path: Path, target_text: str) -> tuple[list[CharSegment], str]:
    """
    Hem forced alignment (target'a göre per-fonem skor) hem de greedy
    transcription (modelin duyduğu serbest metin) doner. İkisi birlikte
    'akustik var ama yanlış kelime' durumunu (forced alignment cömert
    olduğu için) tespit etmemizi sağlar.
    """
    model, processor = _get_model_and_processor()
    audio = load_audio(audio_path)
    emission, vocab = get_emissions(audio, model, processor)

    target, target_orig = normalize_text_for_ctc(target_text, vocab)
    if not target:
        raise ValueError("Hedef metin model sözlüğüyle uyumsuz.")
    tokens = [vocab[c] for c in target]
    blank_id = vocab.get("<pad>", 0)
    trellis = build_trellis(emission, tokens, blank_id)
    path = backtrack(trellis, emission, tokens, blank_id)
    frame_duration_s = len(audio) / SAMPLE_RATE / emission.size(0)
    end_frame = _last_non_blank_frame(emission, blank_id)
    segments = merge_to_chars(path, target, frame_duration_s, target_orig, end_frame)
    transcription = greedy_transcribe(emission, vocab)
    return segments, transcription


def report(segments: list[CharSegment]) -> None:
    print(f"{'char':>6}  {'start':>6}  {'end':>6}  {'score':>6}  status")
    print("-" * 42)
    for s in segments:
        status = "OK" if s.ok else "DUSUK"
        char_display = "_" if s.char == "|" else s.char
        print(f"{char_display:>6}  {s.start_s:>6.2f}  {s.end_s:>6.2f}  {s.score:>6.2f}  {status}")
    avg = sum(s.score for s in segments) / len(segments)
    bad = [s for s in segments if not s.ok and s.char != "|"]
    print()
    print(f"Genel skor: {avg:.2f}")
    if bad:
        print("Sorunlu sesler:", ", ".join(s.char for s in bad))
    else:
        print("Tüm sesler eşik üstü.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--text", type=str, required=True)
    args = parser.parse_args()
    segments = assess(args.audio, args.text)
    report(segments)


if __name__ == "__main__":
    main()
