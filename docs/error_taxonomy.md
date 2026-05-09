# İstanbul Türkçesi Diksiyon Hata Taksonomisi

**Sürüm:** v0.1 (taslak)
**Tarih:** 2026-05-08
**Amaç:** Uygulamanın hangi hataları tespit edip kullanıcıya geri bildireceğini, her bir hatanın tanımını, tipik örneklerini, mevcut sistemde teknik olarak nasıl yakalanabileceğini ve önerilen pedagojik geri bildirimi ortak bir referansta toplamak.

Bu belge **dilbilimci/eğitmen ile birlikte** geliştirilecek. v0.1, mühendislik tarafından kabaca taslaklanmış başlangıç noktasıdır; teknik gerçeklik doğru, dilbilimsel ifadeler eğitmen tarafından gözden geçirilmelidir.

## Sütunlar

| Alan | Anlamı |
|---|---|
| **ID** | Hatanın referans kodu |
| **Tanım** | Hatanın özet açıklaması |
| **Örnek** | Yanlış vs doğru söyleyiş |
| **Tespit** | Mevcut pipeline'ın hangi katmanı yakalar (alignment / prosody / G2P / yok) |
| **Feedback** | Kullanıcıya verilecek metnin önerilen çekirdeği |
| **Öncelik** | M1 = ilk sürüm, M2 = sonraki, M3 = ileri |

---

## A. Ünlü hataları

### A1. Şapkalı ünlü kısaltma (â, î, û)
- **Tanım:** Düzeltme işaretli ünlüler uzun ve ince okunmalıdır; çoğu konuşmacı kısaltır.
- **Örnek:** "kâr" /ka:r/ ↔ "kar" /kar/; "hâlâ" /ha:la:/ ↔ "hala" /hala/.
- **Tespit:** **G2P + alignment** (segment süresi ölçülerek). Süre eşik altıysa hata.
- **Feedback:** "‘â’ harfi uzun okunmalı; ‘kâr’ kelimesi ‘kaar’ gibi düşün."
- **Öncelik:** M1 ✅ (mevcut)

### A2. Kapalı 'e' [ɛ] yerine açık 'e'
- **Tanım:** Belirli ortamlarda 'e' kapalı söylenir (ben, sen, gel, et-, dert). Açık 'e' [e] ile karışınca İstanbul Türkçesi'ne yabancı duyulur.
- **Örnek:** "ben" doğrusu [bɛn], yanlış [ben]; "gel" [gɛl] vs [gel].
- **Tespit:** **Henüz yok** — F1/F2 formant analizi gerekir. (Mevcut wav2vec2 grafem-bazlı, ‘e’ ayrımı yapmaz.)
- **Feedback:** "Bu ‘e’ kapalı bir e; ağzı geniş açma, ‘a’ya doğru kayma."
- **Öncelik:** M2 (formant katmanı eklenmeli)

### A3. 'ı' / 'i' karışması
- **Tanım:** Anadolu ağızlarında 'ı' ile 'i' karıştırılır; İstanbul Türkçesi'nde net ayrılmalı.
- **Örnek:** "İstanbul" değil "Istanbul" (ilk hece); "biraz" değil "bıraz".
- **Tespit:** **Alignment** — yanlış sesletirse skor düşer. Bağlam-özel feedback için G2P ekstra not verir.
- **Feedback:** "‘i’ ön ve ince, ‘ı’ arka ve dudaksız. Karıştırma."
- **Öncelik:** M1 ✅

### A4. 'o' / 'ö', 'u' / 'ü' yuvarlaklık karışması
- **Tanım:** Ön/arka ünlü ayrımı; özellikle bölgesel olarak ön ünlüler arkalaşır.
- **Örnek:** "köpek" → "kopek"; "düşman" → "duşman".
- **Tespit:** **Alignment** (yüksek doğrulukla yakalar).
- **Feedback:** "‘ö’ söylerken dudakları yuvarla ama dili öne al."
- **Öncelik:** M1 ✅

### A5. Yazı-içi olmayan ünlü uzunluğu (Arapça/Farsça kökenli)
- **Tanım:** "memur" (me'mur), "saat" (sa'at) gibi şapkasız ama kökeninde uzun olan ünlüler.
- **Örnek:** "memur" /me:mur/ ↔ /memur/; "saat" /sa:t/ ↔ /sat/.
- **Tespit:** **Lexicon gerekli** — sadece sözlüksel olarak bilinir, kuraldan çıkarılamaz.
- **Feedback:** "Bu kelimedeki ‘e’ uzun okunur; ‘memuur’ gibi düşün."
- **Öncelik:** M2 (uzun-ünlü sözlüğü hazırlanmalı)

### A6. Ünlü düşmesi (yazıdan sapan)
- **Tanım:** "burası" → "burda"; "nereye" → "nere"; konuşma dilinde olabilir, diksiyonda kaçınılmalı.
- **Örnek:** "evine" yerine "evne", "olacak" yerine "olcak".
- **Tespit:** **Alignment** — atlanan ünlü düşük skor verir.
- **Feedback:** "Bu ‘e’ açıkça duyulmalı; düşürme."
- **Öncelik:** M1 ✅

---

## B. Ünsüz hataları

### B1. 'ğ' yanlış telaffuz (gırtlaksıllaştırma)
- **Tanım:** ğ İstanbul Türkçesi'nde sessizdir; bazı konuşmacılar gırtlaktan [ɣ] benzeri ses çıkarır.
- **Örnek:** "dağ" /da:/ ↔ /dağ/ (ğ'yi sertçe söylemek).
- **Tespit:** **G2P + alignment** — ğ etrafında düşük skor + bağlam notu.
- **Feedback:** "‘ğ’ sessiz; önündeki ünlüyü uzatır. Boğazdan çıkarmaya çalışma."
- **Öncelik:** M1 ✅

### B2. 'r' aşırı titretmesi
- **Tanım:** İstanbul Türkçesi'nde söz sonu 'r' tek titreşimle, kontrollü olmalı; aşırı [rrr] tiyatromsudur.
- **Örnek:** "haber" — net 'r', ama "haberrr" değil.
- **Tespit:** **Prosody (süre)** — segment süresi normalin çok üzerindeyse hata.
- **Feedback:** "‘r’yi kontrollü tek titreşimle ver, abartma."
- **Öncelik:** M1 ✅ (kısmen — süre ölçümü var)

### B3. 'r' yutumu (söz sonu)
- **Tanım:** "geliyor" → "geliyo"; ses sonu r düşürülür. Diksiyonda kabul edilmez.
- **Örnek:** "haber" → "habe", "yapıyor" → "yapıyo".
- **Tespit:** **Alignment** — eksik fonem, düşük skor.
- **Feedback:** "‘r’yi söyle, yutma. Yumuşak ama duyulur olmalı."
- **Öncelik:** M1 ✅

### B4. 'h' yutumu
- **Tanım:** "hava", "haber"de h zayıflatılıyor; özellikle söz sonu/hece sonu.
- **Örnek:** "sabah" → "saba", "müthiş" → "mütiş".
- **Tespit:** **Alignment** — h düşük/sıfır skor.
- **Feedback:** "‘h’ duyulmalı; nefesli, açık bir ses."
- **Öncelik:** M1 ✅

### B5. Söz sonu 'n' → 'm' geçişi
- **Tanım:** "evden" → "evdem", özellikle b/p/m'den önce.
- **Örnek:** "bunlar" → "bumlar".
- **Tespit:** **Alignment** — yanlış fonem, düşük skor.
- **Feedback:** "‘n’ ile ‘m’yi karıştırma; dil ucu ön damağa."
- **Öncelik:** M1 ✅

### B6. 'ş' / 's' karışması
- **Tanım:** ş söylerken dudaklar hafif yuvarlanır; s'de düz olmalı.
- **Örnek:** "şu" /ʃu/ ↔ /su/.
- **Tespit:** **Alignment**.
- **Feedback:** "‘ş’ için dudakları hafif yuvarla, ‘s’de düz tut."
- **Öncelik:** M1 ✅

### B7. 'c' / 'ç' ötümlülük
- **Tanım:** c ötümlü, ç ötümsüz; ses tellerinin titreyip titremediği fark.
- **Örnek:** "can" /dʒan/ ↔ "çan" /tʃan/.
- **Tespit:** **Alignment**.
- **Feedback:** "‘c’ söylerken ses telleri titrer, ‘ç’de titremez."
- **Öncelik:** M1 ✅

### B8. 'g' / 'k' ötümlülük
- **Tanım:** g ötümlü, k ötümsüz.
- **Örnek:** "gel" ↔ "kel"; "gül" ↔ "kül".
- **Tespit:** **Alignment**.
- **Feedback:** "‘g’ ötümlü, ‘k’ ötümsüz; net ayır."
- **Öncelik:** M1 ✅

### B9. Söz sonu sertleşmesi (b/p, d/t, c/ç, g/k)
- **Tanım:** Ekleme yapılmazsa söz sonu ünsüz sertleşir: "kitap", "ağaç", "renk". Ek alınca tekrar yumuşar: "kitabı".
- **Örnek:** "kitap" /kitap/ doğrusu, "kitab" yanlış (yazılı 'p' var).
- **Tespit:** **Alignment** — model bunu doğru kavrar.
- **Feedback:** "Söz sonunda ‘p’ duyulur, ‘b’ değil."
- **Öncelik:** M2

### B10. 'l' kalın/ince ayrımı
- **Tanım:** Arka ünlüler yanında l kalın [ɫ], ön ünlüler yanında ince [l]: "bal" vs "el".
- **Örnek:** "bal" → "bel"-tonunda l koymak yanlış.
- **Tespit:** **Henüz yok** (formant ihtiyacı). M2.
- **Feedback:** "‘a’nın yanında ‘l’ daha kalın söylenir."
- **Öncelik:** M2

---

## C. Yazı-konuşma farkı (G2P)

### C1. ğ silinmesi + ünlü uzaması
- **Tanım:** Ünlü+ğ+ünlü/sessiz/sonu kombinasyonunda ğ silinir, önceki ünlü uzar.
- **Örnek:** "dağ" → "daa", "değil" → "diil", "yapacağım" → "yapacaım".
- **Tespit:** **G2P** ✅ (hâlihazırda mevcut)
- **Feedback:** "Bu kelimede ğ sessiz; ‘yapacağım’ → ‘yapacaım’."
- **Öncelik:** M1 ✅

### C2. -acak/-ecek bütünlüğü
- **Tanım:** Diksiyonda "yapacam, gelcem" colloquial; standart "yapacağım, geleceğim" (ğ silinmiş hâliyle).
- **Örnek:** "yapacak" → "yapcak" yanlış; "yapacak" tamamı korunmalı.
- **Tespit:** **Alignment** — eksik ünlü = düşük skor.
- **Feedback:** "Bütün heceleri söyle: ‘ya-pa-cak’, ‘yap-cak’ değil."
- **Öncelik:** M1 ✅

### C3. -iyor varyantları
- **Tanım:** "geliyor" net olmalı; "gelio", "geliyo" yanlış.
- **Örnek:** "yapıyor" → "yapio"/"yapıyo" değil.
- **Tespit:** **Alignment**.
- **Feedback:** "‘-iyor’ekini tam söyle: ‘gel-i-yor’."
- **Öncelik:** M1 ✅

### C4. "değil" özel telaffuzu
- **Tanım:** "değil" → "diil" (ğ silinmiş, e+i kaynaşmış).
- **Tespit:** **G2P istisna** ✅
- **Feedback:** "‘değil’ kelimesi ‘diil’ olarak okunur."
- **Öncelik:** M1 ✅

### C5. Bağlaç ve edatlarda ses kaynaşması
- **Tanım:** "ne yapıyorsun" → "napıyorsun" (kabul edilebilir kayıt değil).
- **Örnek:** "ne haber" → "naber".
- **Tespit:** Kompleks; uyarı niteliğinde G2P notu yeter.
- **Feedback:** "Diksiyonda kelimeleri net ayır: ‘ne yapıyorsun’."
- **Öncelik:** M2

---

## D. Vurgu / Tonlama

### D1. Yer adlarının yanlış vurgusu
- **Tanım:** Çoğu yer adı son hece dışında vurgulanır: "Ánkara" (son değil), "İstánbul" (orta).
- **Örnek:** "AnkáRA" yanlış, "Ánkara" doğru.
- **Tespit:** **Stres-etiketli sözlük + prosody (F0/enerji peak konumu)**. Sözlük yok; v2.
- **Feedback:** "‘Ankara’ kelimesinin vurgusu ilk hecede; ‘AN-ka-ra’."
- **Öncelik:** M2

### D2. -iyor öncesi vurgu
- **Tanım:** "Gélíyor" doğrusu (ı uzun ve vurgulu); "geliyór" yanlış.
- **Tespit:** **Prosody** (uygun referans varsa).
- **Feedback:** "Vurgu ‘-i’ hecesinde, son hecede değil."
- **Öncelik:** M2

### D3. Soru cümlesi tonlaması
- **Tanım:** "Geldin mi?" cümlesinde son hece yükselir; bunu yapmamak monoton soru.
- **Tespit:** **Prosody (F0 eğrisi)** + cümle-düzey analiz.
- **Feedback:** "Soru cümlesinde sondaki ‘mi’yi yükseltici tonla söyle."
- **Öncelik:** M2

### D4. Genel monotonluk
- **Tanım:** Cümle boyunca F0 düz seyrederse, vurgu/duygu yok.
- **Tespit:** **Prosody (F0 varyans).**
- **Feedback:** "Cümleyi düz okuma; anlamı destekleyen yerlerde vurgula."
- **Öncelik:** M2

### D5. Yanlış kelime vurgusu (genel)
- **Tanım:** Türkçede çoğu kelime son hecede vurgulu; yer adları, eklerle istisnalar var.
- **Tespit:** **Prosody + sözlük.**
- **Feedback:** "Bu kelimede vurgu son hecede, ortada değil."
- **Öncelik:** M2

---

## E. Akıcılık / Nefes

### E1. Tereddüt sesleri (eee, ııı)
- **Tanım:** Kelime arasına dolgu sesi sokmak.
- **Tespit:** **Henüz yok** (VAD + non-target sesletim algılama).
- **Feedback:** "‘eeee’ ya da ‘ııı’ gibi sesler ekleme; akışta kal."
- **Öncelik:** M3

### E2. Kelime atlama
- **Tanım:** Cümleden bir kelimenin düşmesi.
- **Tespit:** **Alignment** — toplam segment azlığı + kalan segmentlerde düşük skor.
- **Feedback:** "Bir kelime atlamış olabilirsin: ‘…’"
- **Öncelik:** M1 ✅ (kısmen — toplam kontrol gerek)

### E3. Kelime eklemek / tekrarlamak
- **Tanım:** Hedef metinde olmayan kelime girilir.
- **Tespit:** Reverse alignment — fazla ses, hedefte yok.
- **Feedback:** "Verdiğimiz cümleyi tam söyle, ek koyma."
- **Öncelik:** M2

### E4. Yutkunma / dudak şıkırtısı
- **Tanım:** Konuşma sırasında ağız hareketi sesleri.
- **Tespit:** SNR / non-speech detection.
- **Feedback:** "Daha sessiz ortamda kayıt al."
- **Öncelik:** M3

### E5. Hız (çok hızlı / çok yavaş)
- **Tanım:** Toplam süre referansa göre çok kısa/uzunsa.
- **Tespit:** **Prosody (toplam süre normalize)** ✅
- **Feedback:** "Biraz yavaşla / biraz hızlandır."
- **Öncelik:** M1 ✅

### E6. Soluk yönetimi (uzun cümlede nefes)
- **Tanım:** Uzun cümle ortasında soluksuz kalmak; yanlış yerde nefes almak.
- **Tespit:** Sessizlik aralıklarının pozisyonu.
- **Feedback:** "Virgülden sonra kısa nefes al, ondan önce mümkünse alma."
- **Öncelik:** M2

---

## F. Diğer

### F1. Burundan ses (rinolali)
- **Tanım:** Sesin nazal rezonansa kayması.
- **Tespit:** Spektral analiz; v3.
- **Öncelik:** M3

### F2. Boğaz sertliği / gerginlik
- **Tanım:** Sıkışmış, kısık ses.
- **Tespit:** Spektral.
- **Öncelik:** M3

### F3. Çene tutukluğu
- **Tanım:** Ağzı tam açmadan konuşmak; ünlülerde belirsizlik.
- **Tespit:** Alignment'taki ünlü skorları ile dolaylı.
- **Öncelik:** M2

---

## Özet — Mevcut sistemde durum

| Kategori | M1 hazır | Eksik |
|---|---|---|
| A. Ünlü | A1, A3, A4, A6 | A2 (kapalı e — formant), A5 (uzun ünlü sözlüğü) |
| B. Ünsüz | B1-B8 | B9 (kısmen), B10 (kalın l), söz sonu sertleşme |
| C. Yazı-konuşma | C1, C2, C3, C4 | C5 (kaynaşma) |
| D. Vurgu/Tonlama | E5 (hız) | D1-D5 (referans + sözlük) |
| E. Akıcılık | E2, E5 | E1, E3, E4, E6 |
| F. Diğer | — | F1-F3 |

**M1 (ilk sürüm)** hedefi: A ve B kategorilerinin %80'i + C kategorisinin tamamı. Mevcut sistem bu hedefe yaklaştı.

**M2 hedefi:** Stres-etiketli sözlük + uzun-ünlü sözlüğü + formant katmanı (kapalı e). Eğitmen ile birlikte yapılacak en büyük iş.

**M3 hedefi:** Kelime-üstü tonlama + nefes/akıcılık + spektral analiz.

---

## Eğitmen tarafında yapılacaklar (öncelik sırasıyla)

1. **Liste denetimi:** Yukarıdaki 30 maddeyi profesyonel diksiyon kuralları ışığında doğrula.
2. **Stres-etiketli sözlük (M2):** En sık 1500-2000 kelime için her hecenin vurgu durumu. Yer adları öncelik.
3. **Uzun-ünlü sözlüğü (M2):** "memur, saat, hayat" gibi yazıda gözükmeyen uzun ünlüleri olan kelimeler.
4. **Kapalı 'e' bağlamları (M2):** Hangi kelime/ortamlarda kapalı e söylenir kuralı.
5. **Geri bildirim metinleri:** Her madde için kullanıcıya verilecek metnin doğal Türkçe formu.
6. **Stüdyo referans kayıtları:** İlk 200 alıştırma için altın referans (vurgu/tonlama analizi için temel).

---

## Açık sorular

- "Standart İstanbul Türkçesi" referansı kim — TRT spikeri normu mu, geleneksel diksiyon kitapları mı, akademik fonetik mi? (Bunu eğitmen netleştirmeli.)
- Hangi register destekleniyor: yalnız resmi diksiyon mu, günlük doğal İstanbul Türkçesi de mi? (M1 = resmi.)
- Ağız bölgesel — kullanıcı Anadolu ağzıyla konuşunca "hata" mı, "farklılık" mı diyeceğiz? (Şu an "hata" gibi gösteriyoruz; arayüzde dilimiz yumuşatılabilir.)
