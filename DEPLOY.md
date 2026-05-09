# Deploy

Frontend Vercel'de, backend Hugging Face Spaces'te (ML için tasarlandı, ücretsiz tier yeterli).

## 1. Backend → Hugging Face Spaces

1. https://huggingface.co/new-space → **Docker** SDK seç, görünürlük Public.
2. Space adı: örn. `istanbul-turkcesi`. URL: `https://USERNAME-istanbul-turkcesi.hf.space`
3. HF Space repo'sunu remote olarak ekle ve push'la (`Dockerfile` zaten root'ta hazır):
   ```bash
   git remote add hf https://huggingface.co/spaces/USERNAME/istanbul-turkcesi
   git push hf main
   ```
   (HF kullanıcı adı + token ister. Token: https://huggingface.co/settings/tokens — `write` scope.)
4. İlk build 5–10 dk (model indirme dahil). Bittiğinde aç:
   - `https://USERNAME-istanbul-turkcesi.hf.space/exercises` → JSON listesi gelmeli.
   - `/static/` da çalışır (Space'in kendi içinde de UI servisi var).

> **Veri notu:** `data/exercises/refs/`, `data/knowledge/word_clips/` git'te yok (`.gitignore`).
> Bu dosyalar olmadan `/assess` çalışır ama `/reference/` ve `/word-clip/` 404 verir.
> Tam çalışma için ya bu klasörleri HF Hub dataset olarak ayrı yükleyip Space başlangıcında
> indir, ya da git LFS ile push'la (HF Spaces 50 GB'a kadar destekler).

## 2. Frontend → Vercel

1. https://vercel.com/new → bu GitHub repo'sunu import et.
2. **Framework Preset:** Other. Diğer ayarlar default — `vercel.json` zaten outputDirectory'yi belirliyor.
3. Deploy et. İlk URL: `https://istanbul-turkcesi-app.vercel.app` gibi.
4. **Backend URL'sini bağla:** `vercel.json` dosyasındaki tüm `CHANGE-ME-HF-USERNAME-istanbul-turkcesi.hf.space`
   stringlerini gerçek HF Space URL'inle değiştir, commit + push. Vercel otomatik redeploy eder.

   Hızlı yol (Windows PowerShell):
   ```powershell
   $hf = "USERNAME-istanbul-turkcesi.hf.space"
   (Get-Content vercel.json) -replace 'CHANGE-ME-HF-USERNAME-istanbul-turkcesi\.hf\.space', $hf | Set-Content vercel.json -Encoding utf8
   git add vercel.json; git commit -m "wire frontend to HF backend"; git push
   ```

## Neden böyle?

- **Vercel** static + serverless için hızlı, global CDN. Ama 100MB/10sn limitleri var → wav2vec2 sığmaz.
- **HF Spaces** ML modelleri için tasarlandı, Docker desteği var, model cache built-in. Ücretsiz tier'da CPU + 16GB RAM, 2 saatlik inactivity sonrası uyur (ilk istek ~30sn cold start).
- Vercel `rewrites` API çağrılarını HF'ye proxy'ler — frontend kodu `location.origin`'ı kullanmaya devam eder, **CORS sorunu yok**.

## Cold start'ı azaltmak için

HF Space ücretsiz tier'da uyur. Üç seçenek:
- **HF Pro tier** ($9/ay): Sleep yok.
- **Cron ping**: GitHub Actions ile dakikada bir `/exercises` ping at, uyumasını engelle.
- **Modal/Replicate** gibi alternatif: Daha hızlı cold start ama paid.
