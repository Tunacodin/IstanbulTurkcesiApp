# Kayıt Öncelik Listesi — Mennan Şahin tarzı İstanbul Türkçesi

Kullanıcının kendisi (veya bir profesyonel seslendirmen) tarafından kaydedilecek
kelime/cümle/tekerleme/paragraf listesi. Diksiyon müfredatlarının çapraz
incelenmesinden elde edildi — birden fazla kaynakta geçen yüksek öncelikli
itemler.

## Kaynaklar (çapraz kontrol edilen)

1. **MEB** — Konuşma Eğitimi (Diksiyon) Resmi Kurs Programı (2012)
2. **Karmer / Gaziosmanpaşa Üniv.** — Alıştırmalar ve Uygulamalar (Topçuoğlu & Özden)
3. **Diksiyon Akademi** — 98 sayfa Diksiyon Kitabı (2017)
4. **Sinema Akademi** — En Çok Hatalı Söylenen Sözcükler tablosu
5. **Ülkü Giray (TRT spiker rehberi)** — referans
6. **Wikipedia** — Türkçede sık yapılan hatalar
7. **diksiyontv.com** (Mennan Şahin) — eğitmen serisi (zaten elimizde 1498 kelime)

## Kayıt sırası

Her dosya 1 oturumluk yaklaşık iş yükü (~30 dk):

| # | Dosya | İçerik | Tier |
|---|---|---|---|
| 01 | [hatali_sozcukler.md](01_hatali_sozcukler.md) | Hatalı→doğru çiftleri (en yaygın 70 kelime) | **HOT** |
| 02 | [uzun_unluler.md](02_uzun_unluler.md) | â/î/û içeren kelimeler (~80) | **HOT** |
| 03 | [vurgu_yer_adlari.md](03_vurgu_yer_adlari.md) | Yer adları (vurgu ilk hecede, ~30) | HIGH |
| 04 | [vurgu_zarf_baglac.md](04_vurgu_zarf_baglac.md) | Zarf/bağlaç (vurgu ilk hecede, ~30) | HIGH |
| 05 | [bogumlama_sorunlu.md](05_bogumlama_sorunlu.md) | Atlama yapılan kelimeler (~40) | HIGH |
| 06 | [tekerlemeler.md](06_tekerlemeler.md) | 26 harf × 1 tekerleme + klasikler | MED |
| 07 | [paragraflar.md](07_paragraflar.md) | Soğuk okuma metinleri | LOW |

## Kayıt teknik notu

- 16 kHz mono WAV
- Sessiz oda, popfilter (önemli)
- Her kelime arasında ~500 ms sessizlik (kesim için)
- Doğal hız, doğal vurgu — abartılı sahne sesi değil
- Cümle/tekerleme: tek seferde, doğal akıcılıkta
- Dosya adı: `<normalize_word>.wav` (örn. `merhaba.wav`, `sukoseyazkosesi.wav`)
- Word_clips_index.json otomatik üretilir (`build_word_clips_index.py` benzeri)

## Toplam yük

~250 kelime + ~30 tekerleme + 5-10 paragraf = **~3-4 saatlik kayıt seansı** (dikkatli, marjlı)
