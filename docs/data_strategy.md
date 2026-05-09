# Veri Stratejisi

## Soru

YouTube'daki diksiyon eğitmeni videolarındaki konuşmacı sesi + YT'nin sağladığı
transcript bilgisi (zaman damgalı) eğitim/referans verisi olarak kullanılabilir mi?

## Cevap (özet)

Evet, ama **eğitim verisi olarak değil, referans/doğrulama verisi olarak**.
Üç sebep:

1. **Word-level timestamp yok.** YT transcript'i ifade seviyesinde — bizim
   foneme kadar inmemiz gerekiyor. O yüzden YT timestamp'i sadece "kaba
   konum" verir; üzerine kendi forced alignment'ımızı koşmak şart.
2. **Telif gri alan.** YT ToS'u indirmeyi yasaklıyor; ticari ürün için
   kanal sahibi izni veya CC lisansı şart.
3. **Modelimiz zaten Türkçe biliyor.** `mpoyraz/wav2vec2-xls-r-300m-cv8-turkish`
   Common Voice TR ile fine-tune edilmiş; ek eğitim verisine ihtiyacımız yok.

## Üç kullanım modeli — değer sırasıyla

### 1. Altın referans kayıtları (yüksek değer)
Küratörlüğünü yaptığımız alıştırma havuzundaki kelime/cümleleri YT'de
geçtiği yerden kes, eğitmenin söylediği şekliyle **referans** olarak sakla.
Kullanıcının kaydı bu referansla F0 + süre + enerji üzerinden kıyaslanır
(DTW). Vurgu hatasının ana sinyali bu.

### 2. POC doğrulama seti (orta değer)
Birkaç dakika temiz spiker konuşması + transcript ile pipeline'ı test et.
Yüksek skor vermesi gerek; vermiyorsa pipeline'da hata var.

### 3. Öğretim materyali (sunum değeri)
"Yanlış vs doğru" gösteren videolardan kesitler — uygulamada kullanıcıya
"böyle olmaz, böyle olur" örnekleri olarak göster. Ses analizi değil
gösterim katmanı için.

## Açık Türkçe veri setleri (model fine-tuning gerekirse)

| Veri seti | Boyut | Lisans | Yorum |
|---|---|---|---|
| Common Voice TR (Mozilla) | 134 saat | CC0 | Geniş ama karışık ağız |
| Turkish Broadcast News (Boğaziçi) | ~130 saat VOA | Akademik | Spiker Türkçesi |
| `issai/Turkish_Speech_Corpus` | HF | Apache 2.0 | Çoklu konuşmacı |
| Open_SLR108_TR | 10 saat | CC | Küçük ama temiz |
| `mpoyraz/wav2vec2-turkish` (model) | — | Apache 2.0 | Bizim baz modelimiz |

Bunlar zaten model eğitiminde kullanılmış. POC'de ek fine-tune yapmıyoruz.

## YouTube veri toplama akışı (izin alındığında)

```
URL + hedef ifade listesi
        │
        ▼
yt-dlp ile en kaliteli ses (m4a/wav, 16 kHz)
        │
        ▼
youtube-transcript-api ile TR transcript (ifade seviyesi)
        │
        ▼
Hedef ifadeleri transcript'te eşleştir
        │
        ▼
Kaba kesit (transcript zaman damgaları)
        │
        ▼
Wav2Vec2 CTC forced alignment (kelime seviyesi)
        │
        ▼
Temiz kesit + kelime/fonem zaman damgaları
        │
        ▼
data/reference_audio/<exercise_id>.wav + .json (metadata)
```

Aracın kodu: [poc/extract_reference_from_youtube.py](../poc/extract_reference_from_youtube.py)

## Yasal çerçeve

- **POC / iç test:** Gri alan, tolere ediliyor.
- **Ticari ürün:**
  - Kanal sahibi izni (e-posta + sözleşme), veya
  - YT "Creative Commons" filtrelenmiş içerik, veya
  - Kendi stüdyo kayıtlarımız (en temiz çözüm).
- **Common Voice / OpenSLR:** Lisans dostu, doğrudan kullanılabilir.

## Önerilen yaklaşım

1. **MVP referans havuzu küçük tutulur:** İlk 100-200 alıştırma için
   küçük bir stüdyo seansı (1-2 gün, profesyonel diksiyon eğitmeni) en
   temiz çözüm. Bu, tüm YT lojistiğinden ucuza ve hızlıya gelir.
2. **YouTube veri toplama aracı hazır olsun ama** sadece izinli/CC
   içerik için koşturulsun. Genişlemede kullanılabilir.
3. **Kullanıcı verisi:** Uygulama içinde toplanan kayıtlar (kullanıcı
   onayıyla, GDPR/KVKK uyumlu) — gelecekte fine-tuning için en değerli
   veri kaynağı bu olacak.
