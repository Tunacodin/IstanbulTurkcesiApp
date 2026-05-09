---
title: Istanbul Turkcesi Diksiyon
emoji: 🎤
colorFrom: gray
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Turkish pronunciation assessment with wav2vec2
---

# İstanbul Türkçesi Diksiyon

Standart İstanbul Türkçesi telaffuz değerlendirmesi yapan, eğitmen tarzı geri
bildirim üreten web/PWA uygulaması. Sıfırdan model eğitilmedi; off-the-shelf
wav2vec2 + Praat + dilbilimsel kural seti üzerine kuruldu.

## Hızlı başlangıç

```powershell
# Bağımlılıklar (ilk kurulum)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r poc/requirements.txt

# HTTP modu (PC'den test)
.\run.ps1                       # http://127.0.0.1:8765/static/

# HTTPS modu (telefon dahil — PWA için gerekli)
.\run-https.ps1                 # https://localhost:8765/static/
                                # https://<lan-ip>:8765/static/  (telefondan)
```

Detaylı mobil rehber: [docs/MOBIL_KULLANIM.md](docs/MOBIL_KULLANIM.md)

## Mimari

```
Kullanıcı sesi (mikrofon, web)
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  Pipeline (poc/align_and_score.py + prosody.py)          │
│                                                            │
│  1. Forced alignment (wav2vec2-tr CTC)                    │
│     → Per-fonem zaman damgaları + GOP skor                │
│                                                            │
│  2. Greedy CTC transcribe                                 │
│     → "Modelin duyduğu" serbest metin                     │
│                                                            │
│  3. Prosody (librosa + Praat/parselmouth)                 │
│     → F0 dinamiği, intensity range, HNR                   │
│     → Konuşma hızı, kelime içi pause, hece dengesi        │
└──────────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  Feedback (poc/feedback.py)                               │
│                                                            │
│  • Word-level diff (Levenshtein)                          │
│  • Lexicon kontrolü (bilinen R/H yutulması, ünsüz değişim)│
│  • Uzun ünlü süre kontrolü (â/î/û)                        │
│  • Naturalness eşikleri (monoton, hızlı, tutuk, hırıltılı)│
└──────────────────────────────────────────────────────────┘
        │
        ▼
   JSON cevap → UI (kelime bazlı kırmızı vurgu, tıkla→tooltip)
```

## Özellikler

### Telaffuz değerlendirmesi
- **Fonem-bazlı skor:** Her sesin akustik benzerliği
- **Word-level mismatch:** Hangi kelime yanlış söylendi
- **Bilinen diksiyon kalıpları:** R yutulması, H yutulması, k↔g/t↔d gibi ünsüz değişimleri (Anadolu ağzı işaretleri)
- **Uzun ünlü kontrolü:** â/î/û için minimum süre eşiği

### Konuşma tarzı (referansa bağımsız)
- **Monotonluk:** F0 dinamik aralığı (semitone)
- **Konuşma hızı:** karakter/saniye, eğitmen aralığına göre kalibre
- **Hırıltılı/temiz ses:** HNR (Praat)
- **Vurgu kapasitesi:** Intensity range (Praat)
- **Hece hece bölme:** Kelime içi pause tespiti
- **Hece dengesi:** Süre varyasyon katsayısı

### İçerik
- 10+ alıştırma (kelime, cümle, tekerleme, paragraf)
- TTS (Edge tr-TR) referans sesleri
- Diksiyon eğitmen videolarından kelime bazlı telaffuz örnekleri
- 65+ kelime/okunuş çifti, 21 hata desen sözlüğü, ~70 vurgu kuralı

### UI / PWA
- Kelime bazlı kırmızı vurgu + tıkla→detay tooltip
- Hata tipine göre renk (R yutulması sarı, kritik ünsüz turuncu, vb.)
- "Doğru telaffuzu dinle" — tüm cümle TTS
- "Kelime bazlı dinle" — her kelimenin yanında ▶ butonu, eğitmen videosu kesiti
- Telefonda PWA: ana ekrana ekle, fullscreen, offline cache

## Klasör yapısı

```
IstanbulTurkcesiApp/
├── poc/                          # Python backend + UI
│   ├── align_and_score.py        # Forced alignment + transcription
│   ├── feedback.py               # Geri bildirim üreteci (skor + advice)
│   ├── prosody.py                # F0, intensity, HNR, naturalness
│   ├── lexicon.py                # Lexicon yükleyici + pattern matching
│   ├── g2p.py                    # Grapheme-to-phoneme (yazı→telaffuz)
│   ├── stress.py                 # Hece bölme + vurgu yeri tahmini
│   ├── api.py                    # FastAPI service (REST + static UI)
│   ├── static/                   # Web UI + PWA (manifest, sw.js, icons)
│   ├── generate_cert.py          # Self-signed TLS (PWA için)
│   ├── generate_icons.py         # PWA ikon üretici
│   ├── generate_references.py    # Edge TTS ile referans sesi üret
│   ├── make_tts_samples.py       # Test için TTS örnek üret
│   ├── extract_reference_from_youtube.py  # YT'den referans çıkarıcı
│   ├── search_cc_youtube.py      # CC-lisanslı YT arayıcı
│   ├── download_youtube_audio.py # Knowledge için YT ses indirici
│   ├── fetch_youtube_knowledge.py # YT transcript arşivleyici
│   ├── build_word_clips_index.py # Kelime bazlı eğitmen telaffuz indeksi
│   ├── extract_lexicon_from_transcripts.py  # Regex aday çıkarıcı
│   ├── llm_extract_lexicon.py    # Claude API ile yapısal extraction
│   ├── analyze_youtube_pace.py   # Eğitmen hız istatistikleri
│   └── requirements.txt
│
├── data/
│   ├── exercises/                # Alıştırma metinleri + referans wav'lar
│   ├── lexicon/                  # G2P, error patterns, stress, ilkeler
│   │   ├── g2p_pairs.json        # 65 yazı/okunuş çifti
│   │   ├── error_patterns.json   # R/H yutulması örnekleri
│   │   ├── stress_lexicon.json   # Vurgu kuralları + sözcükler
│   │   ├── diksiyon_ilkeleri.json # Pedagojik temel ilkeler
│   │   └── pace_stats.json       # YT'den çıkarılan eğitmen hızı
│   ├── knowledge/                # YT'den arşivlenen içerik
│   │   ├── youtube_transcripts/  # 4 video transcript JSON
│   │   ├── youtube_audio/        # 3 video ses (wav 16kHz)
│   │   ├── word_clips/           # Kelime bazlı kesitler
│   │   └── word_clips_index.json # Kelime → (video, start, end) indeksi
│   └── validation_set/           # Test seti (TTS örnekler)
│
├── docs/
│   ├── architecture.md           # Mimari notları
│   ├── data_strategy.md          # Veri toplama stratejisi
│   └── MOBIL_KULLANIM.md         # Telefonda PWA kullanım rehberi
│
├── run.ps1                       # HTTP başlatıcı
├── run-https.ps1                 # HTTPS başlatıcı (PWA / telefon için)
└── README.md
```

## API endpoint'leri

| Endpoint | Method | Açıklama |
|---|---|---|
| `/` | GET | Health check |
| `/exercises` | GET | Alıştırma havuzu |
| `/reference/{id}` | GET | Alıştırma için referans ses (wav) |
| `/assess` | POST | Mikrofon kaydı + target → skor + feedback JSON |
| `/available-clips` | GET | Eğitmen videosundan sesi olan kelimelerin listesi |
| `/word-clip/{word}` | GET | Kelimenin gerçek diksiyon eğitmeni telaffuz örneği (wav) |
| `/word-clip-info/{word}` | GET | Kelimenin meta bilgisi (kaynak video, bağlam) |

## Bilinen sınırlar

1. **Skor eşikleri sezgisel**: `LONG_VOWEL_DURATION_RATIO=1.4`, mismatch_floor=0.10,
   word error caps (0.70/0.50/0.30) gerçek kullanıcı verisi gelince ayarlanmalı.
2. **TTS referansları geçici**: Edge TTS â'yı yeterince uzatmıyor; eğitmen
   stüdyo kayıtlarıyla değiştirilecek.
3. **CPU bağımlı**: 8 saniyelik ses ~3.5 saniye işliyor. Mobil real-time için
   GPU veya quantized model lazım.
4. **Lexicon küçük**: 65 kelime + 21 hata deseni. LLM ile transcript parsing
   yapıldığında 500+'a çıkacak.
5. **Vurgu yeri tahmini var ama ölçümü yok**: Sözlük + heuristik vurgu yerini
   tahmin ediyor; ses üzerinde gerçek vurgu ölçümü (F0/enerji peak'i) henüz yok.

## Sonraki adımlar (öncelik sırası)

1. **Kullanıcı pilot testi** — 5-10 kişiyle sistem doğrulanması, eşik kalibrasyonu.
2. **LLM ile transcript parsing** — 4 video × 27 dakika içerik → 500+ kelime,
   100+ kural otomatik çıkarımı (Claude API + `llm_extract_lexicon.py`).
3. **Eğitmen stüdyo kayıtları** — TTS yerine 200+ alıştırmanın profesyonel kaydı.
4. **Vurgu yeri ölçümü** — F0 + enerji peak'i ile gerçek vurgu tespiti, sözlükle kıyas.
5. **Public hosting** — Render/Railway gibi cloud, telefondan / başka kullanıcılardan erişim.
6. **Native mobil** — App Store/Play Store, gelecek aşamada.

## Lisans / kaynaklar

- Wav2Vec2 modeli: `mpoyraz/wav2vec2-xls-r-300m-cv8-turkish` (Apache 2.0)
- Praat: parselmouth (GPL3 — research/POC için uygun, ticari ürün için lisans kontrolü)
- Edge TTS: Microsoft (geçici referans, ticari ürün için yerine eğitmen kaydı koy)
- YT içerikleri: "Diksiyon Dersleri" kanalı — POC için kullanım, ticari ürün için
  içerik sahibinden izin gerek
