# Mimari Notları

## Çekirdek varsayım

Hedef metin önceden bilinmektedir. Bu, problemi "speech recognition"dan
"speech alignment + scoring"e indirger — çok daha kolay, ML eğitimi gerektirmez.

## Boru hattı

### 1. Ön işleme
- Mono, 16 kHz'e resample.
- Sessizlik kırpma (VAD veya basit enerji eşiği).
- Ses kalitesi kontrolü: SNR < 10 dB ise kullanıcıya yeniden kayıt iste.

### 2. Forced alignment
- Model: `mpoyraz/wav2vec2-xls-r-300m-cv8-turkish` veya benzer Türkçe wav2vec2.
- Yöntem: hedef metni karakter veya fonem dizisine çevir, CTC posterior'larından
  trellis hizalama (HuggingFace tutorial: "Forced Alignment with Wav2Vec2").
- Çıktı: her karakter/fonem için (start_time, end_time, score).

### 3. Skor (GOP — Goodness of Pronunciation)
- Her fonem için: `log p(beklenen_fonem | ses_segmenti)`.
- 0–1 arası normalize edilmiş skor.
- Eşik (örn. 0.7) altındakiler "düzeltilmesi gereken" olarak işaretlenir.

### 4. Referans karşılaştırma (opsiyonel, vurgu için)
- Eğitmenin altın kaydı → F0 eğrisi, enerji eğrisi, fonem süreleri.
- Kullanıcı kaydı için aynı çıkarım.
- Dynamic Time Warping ile hizalama, sapma metrikleri.
- Vurgu/tonlama hatasının ana sinyali.

### 5. Geri bildirim üretimi
- Kural tabanlı şablonlar yeterli:
  - `"<kelime> kelimesinde <hece> hecesi düşük skorlu (0.42). Tekrar dener misin?"`
- LLM yalnızca mesajı doğal hale getirmek için (opsiyonel, ucuz model).

## Türkçeye özgü incelikler

### Yazı–konuşma farkı
- Türkçe oldukça fonetik bir yazı sistemi ama:
  - "değil" → "diil"
  - "yapacağım" → "yapıcam"
- Çözüm: hedef metni telaffuz formuna çevirip alignment'ı o forma göre yap.
- Bunun için bir **G2P (grapheme-to-phoneme) modülü** lazım — küçük bir kural
  seti + istisnalar sözlüğü ile başlanabilir.

### Vurgu
- Genel kural: son hece. Ama istisnalar:
  - Yer adları (Ánkara, İstánbul)
  - "-iyor" ekinden önce
  - Soru ekleri
  - Yabancı kökenli kelimeler
- **Stres-etiketli sözlük** projenin gerçek dilbilimsel mülkiyeti olacak.

### Uzun ünlülü kelimeler
- Arapça/Farsça kökenli: "kâr", "hâlâ", "âlim" → düzeltici işaret olmadan da
  uzun okunmalı. Süre ölçümü ile kolay tespit.

### Kapalı e
- "geliyor"daki e [e] değil [ɛ]/[æ] arası.
- Standart fonem alfabesi her zaman ayırmaz; formant analizi (F1/F2) ile
  ek bir kontrol gerekebilir. POC kapsamı dışında.

## Veri ihtiyaçları

| Veri | Miktar (MVP) | Kaynak |
|---|---|---|
| Alıştırma metinleri | 100–300 kelime/cümle/tekerleme | Diksiyon kitapları (Şenbay vb.) |
| Eğitmen altın kayıtları | Aynı sayıda | YouTube videolarından kesit (telifi netleştir) veya kendi stüdyo kaydımız |
| Stres-etiketli sözlük | 2000+ kelime | Manuel + dilbilimci |
| Test kullanıcı kayıtları | 20+ kişi × 50 alıştırma | Kapalı beta |

## Dağıtım

- **Backend:** FastAPI, model ses kartı yokluğunda CPU'da da çalışır
  (wav2vec2 tek cümle için ~1 sn).
- **Latency hedefi:** kayıt sonrası ≤ 3 sn.
- **Mobil:** Flutter — Android + iOS tek kod tabanı, ses kaydı için iyi
  paketler mevcut.
