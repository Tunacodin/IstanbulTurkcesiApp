# Telefonda Çalıştırma (PWA)

PWA = Progressive Web App. Telefon tarayıcısından açıp "ana ekrana ekle"
diyerek **uygulama gibi** çalıştırabilirsin. App Store/Play Store'a yüklemek
gerekmez, klasik mobil app geliştirme maliyeti yok.

## Tek seferlik kurulum (PC tarafında)

1. PC ve telefon **aynı Wi-Fi'da** olmalı.
2. Windows Güvenlik Duvarı 8765 portunu blokluyor olabilir; ilk başlatmada
   "Erişime izin ver" gelirse onayla.
3. Self-signed TLS sertifikası gerekiyor (HTTPS, çünkü mikrofon ve service
   worker localhost dışında HTTP'de çalışmaz). Aşağıdaki script otomatik
   üretiyor.

## Çalıştırma

```powershell
.\run-https.ps1
```

Çıktıda iki adres göreceksin:
- `https://localhost:8765/static/` (PC'den)
- `https://192.168.x.y:8765/static/` (telefondan)

Telefonun tarayıcısında ikincisini aç.

## Telefonda yapacakların

### 1. Sertifika uyarısını geç
Self-signed sertifika olduğu için **"Bu site güvenli değil"** uyarısı çıkar.
- Chrome/Edge: "Gelişmiş" → "Yine de devam et"
- Safari (iOS): "Ayrıntıları göster" → "Bu siteyi ziyaret et" → "Ziyaret et"

(Kendi geliştirme ortamında güvenli; yabancı bir siteye bunu yapma.)

### 2. Mikrofon izni
Kayıt başlatınca tarayıcı izin ister, **"İzin ver"**.

### 3. Ana ekrana ekle
PWA olarak çalışsın, ikon ana ekranda dursun:

- **Android (Chrome):** Adres çubuğunun yanındaki üç nokta → **"Ana ekrana ekle"** veya "Uygulamayı yükle".
- **iOS (Safari):** Paylaş butonu (kare + yukarı ok) → **"Ana Ekrana Ekle"**.

İkonu ekledikten sonra normal uygulama gibi açılır — tam ekran, üst tarayıcı çubuğu yok.

## Sınırlar (PWA vs Native)

| Özellik | PWA | Native |
|---|---|---|
| Mikrofon | ✅ | ✅ |
| Ses oynatma | ✅ | ✅ |
| Offline (alıştırma listesi + referans sesler) | ✅ (service worker cache) | ✅ |
| Push bildirim | ✅ Android, ⚠️ iOS sınırlı | ✅ |
| Background kayıt | ❌ | ✅ |
| App Store yayını | ❌ (link paylaşırsın) | ✅ |
| Geliştirme süresi | 1-2 saat (mevcut) | 6-8 hafta |

POC ve ilk kullanıcı testleri için PWA fazlasıyla yeterli.

## Sorun giderme

**Telefonda sayfa açılmıyor:**
- PC'nin LAN IP'si değişmiş olabilir (DHCP). `ipconfig` ile kontrol et,
  `run-https.ps1` her başlatmada IP'yi otomatik bulur ama sertifika eski
  IP için olabilir. `poc/certs/` klasörünü silip yeniden çalıştır → cert
  güncel IP ile üretilir.
- Windows Güvenlik Duvarı: Denetim Masası → Güvenlik Duvarı → "Bir
  uygulamaya izin ver" → Python.exe için Public/Private ikisini de işaretle.

**Mikrofon çalışmıyor:**
- HTTPS şart (HTTP'de Chrome/Safari mikrofon vermez). `https://...` ile
  açtığından emin ol.
- Tarayıcı izin geçmişini kontrol et: Site ayarları → Mikrofon → İzin ver.

**"Ana ekrana ekle" görünmüyor:**
- Sayfa en az bir kez tam yüklenmeli (manifest fetch'lenir).
- iOS'ta sadece **Safari** PWA yükler (Chrome/Firefox iOS'ta yüklemiyor).
