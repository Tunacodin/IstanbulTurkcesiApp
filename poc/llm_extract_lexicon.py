"""LLM (Claude) ile YT diksiyon transkriptlerinden yapilandirilmis
kelime/kural kayitlari cikar.

Onkosul:  ANTHROPIC_API_KEY ortam degiskeni ayarli olmali.
    PowerShell:  $env:ANTHROPIC_API_KEY = "sk-ant-..."
    Kalici:      [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-...", "User")

Kullanim:
    python llm_extract_lexicon.py            # tum transkriptleri isle
    python llm_extract_lexicon.py --dry-run  # API cagrisi yapma, sadece prompt gostermek icin

Cikti:
    data/lexicon/llm_extracted.json   (her video icin yapilandirilmis kayitlar)

Maliyet: Claude Sonnet 4.6 ile ~27 dakika transkript icin tahmini $0.10-$0.30.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TX_DIR = REPO_ROOT / "data" / "knowledge" / "youtube_transcripts"
OUT = REPO_ROOT / "data" / "lexicon" / "llm_extracted.json"

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """Sen bir Türkçe dilbilim asistanısın. İstanbul Türkçesi diksiyon eğitimi
videosunun transkriptini parse edip YAPILANDIRILMIŞ veri çıkaracaksın.

Çıkarman gereken bilgi türleri:

1. **Kelime telaffuz çiftleri** — eğitmen "X yerine Y", "X değil Y", "X şeklinde
   okunur" gibi yapılarla bahsettiği kelimeler. Burada eğitmen genelde aynı yazımı
   iki farklı şekilde söylüyor (yazım YT auto-caption'da yansımıyor); önemli olan
   eğitmenin kuralı ne anlattığı:
   - "Bağırmak yerine bağırmak" → eğitmen birinci kez kısa, ikinci kez uzun a ile söylüyor
     ⇒ kayıt: {"yazi": "bağırmak", "telaffuz": "ba:ırmak", "kural": "ğ silinir, a uzar"}
   - "Kâğıt değil kaat" → kayıt: {"yazi": "kâğıt", "telaffuz": "ka:t",
                                  "kural": "â + ğ silinir, uzun a"}

2. **Genel kurallar** — eğitmen "şöyle bir kural var" diyerek anlattığı kurallar.
   Örnek: "ğ harfi sessizdir; önündeki ünlüyü uzatır" → genel kural kaydı.

3. **Yaygın yanlışlar** — "Anadolu ağzında", "yanlış kullanım", "şöyle deniyor ama
   doğrusu" gibi ifadelerle bahsedilen hatalar.

ÇIKTIYI SADECE JSON OLARAK VER. Şu yapıyı kullan:

```json
{
  "kelime_ciftleri": [
    {
      "yazi": "kâğıt",
      "telaffuz": "ka:t",
      "kural_adi": "uzun_unlu_g_silme",
      "kural_aciklamasi": "â'dan sonra ğ silinir, a uzun kalır",
      "kaynak_dakika": 0.5,
      "alintilanan_baglam": "Kağıt değil kaat şeklinde söyleriz"
    }
  ],
  "genel_kurallar": [
    {
      "baslik": "ğ ünsüzü",
      "aciklama": "ğ sessizdir; önündeki ünlüyü uzatır",
      "ornekler": ["bağ", "doğa", "kâğıt"],
      "kaynak_dakika": 1.2
    }
  ],
  "yaygin_yanlislar": [
    {
      "yanlis_telaffuz": "Geliyo",
      "dogru_telaffuz": "Geliyor",
      "tip": "r_yutulmasi",
      "aciklama": "Konuşma dilinde -yor sonu r düşürülür ama doğru söylenişte r duyulur",
      "kaynak_dakika": 2.4
    }
  ]
}
```

KURALLAR:
- Sadece transkriptte AÇIKÇA geçen bilgileri çıkar; uydurma.
- "kaynak_dakika" yaklaşık olabilir; transkripteki anki bağlama yakın bir saniye/60.
- Türkçe karakterleri (â, ğ, ş, ı vb.) doğru kullan.
- Telaffuz formunda ":" uzun ünlü işareti.
- ":sadece bir tek anahtar kelimeli kayıt yapma; bağlamı oku."""


USER_PROMPT_TEMPLATE = """Aşağıdaki transkript {title} ({duration_s} saniye) videosundan.
Yukarıdaki yönergeye göre yapılandırılmış JSON çıktısı ver.

[Transkript - zaman damgalı]

{transcript_lines}
"""


def fetch_with_claude(client, title: str, duration_s: int, transcript: list[dict]) -> dict:
    """Tek videonun transkriptini Claude API'sine gonder."""
    # Transcript'i kompakt formatta:  "[12.3s] kelime kelime"
    lines = []
    for seg in transcript:
        start = seg.get("start", 0.0)
        text = seg.get("text", "").strip()
        lines.append(f"[{start:.1f}s] {text}")
    transcript_str = "\n".join(lines)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        title=title,
        duration_s=duration_s,
        transcript_lines=transcript_str,
    )

    message = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=[
            {"type": "text", "text": SYSTEM_PROMPT,
             "cache_control": {"type": "ephemeral"}},  # prompt cache
        ],
        messages=[
            {"role": "user", "content": user_prompt},
        ],
    )

    text = message.content[0].text.strip()
    # Bazen LLM ```json ... ``` ile sarmalar
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        return {"_parse_error": str(exc), "_raw_response": text[:500]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="API çağırma; sadece prompt önizleme")
    args = parser.parse_args()

    if not args.dry_run and not os.environ.get("ANTHROPIC_API_KEY"):
        print("HATA: ANTHROPIC_API_KEY ortam değişkeni ayarlı değil.")
        print('Geçici (oturum):  $env:ANTHROPIC_API_KEY = "sk-ant-..."')
        print('Kalıcı:  [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-...", "User")')
        sys.exit(1)

    client = None
    if not args.dry_run:
        from anthropic import Anthropic
        client = Anthropic()

    all_results = {}
    for path in sorted(TX_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        vid = data["video_id"]
        title = data.get("title", "?")
        duration = int(data.get("duration_s") or 0)
        transcript = data.get("transcript", [])
        print(f"\n→ {vid}  '{title}'  ({duration}s, {len(transcript)} segment)")

        if args.dry_run:
            print(f"  [dry-run] Prompt boyutu: ~{len(json.dumps(transcript))} karakter")
            continue
        try:
            result = fetch_with_claude(client, title, duration, transcript)
            all_results[vid] = {
                "title": title,
                "duration_s": duration,
                "extracted": result,
            }
            n_pairs = len(result.get("kelime_ciftleri", [])) if isinstance(result, dict) else 0
            n_rules = len(result.get("genel_kurallar", [])) if isinstance(result, dict) else 0
            n_errors = len(result.get("yaygin_yanlislar", [])) if isinstance(result, dict) else 0
            print(f"  ✓ {n_pairs} kelime çifti, {n_rules} kural, {n_errors} yaygın yanlış")
        except Exception as exc:
            print(f"  ✗ HATA: {exc}")
            all_results[vid] = {"title": title, "_error": str(exc)}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({
            "_meta": {
                "model": MODEL,
                "kaynak": "4 YT diksiyon transkripti, Claude API extraction",
                "kullanim": "Manuel review sonrası lexicon dosyalarına aktarılır",
            },
            "videos": all_results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nKaydedildi: {OUT}")


if __name__ == "__main__":
    main()
