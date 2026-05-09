"""index.html'deki BENTO STUDIO override blogunu sil,
yerine sade Linear/Vercel-tarzi clean SaaS UI override koy."""

from pathlib import Path

INDEX = Path(__file__).parent / "static" / "index.html"

CLEAN_OVERRIDE = '''
<!-- ============================================================
     Clean SaaS UI — Override layer
     - Notrik palet (siyah/beyaz/gri); skor icin minimal yesil/turuncu/kirmizi
     - Standart responsive grid (3/2/1 kolon)
     - Inter typography (sadece bu)
     - Sade kart tasarimi: 1px border, hover'da minimal shadow
     ============================================================ -->
<style>
  :root, :root * {
    --background: 0 0% 100%;
    --foreground: 0 0% 9%;
    --card: 0 0% 100%;
    --card-foreground: 0 0% 9%;
    --popover: 0 0% 9%;
    --popover-foreground: 0 0% 98%;
    --primary: 0 0% 9%;
    --primary-foreground: 0 0% 98%;
    --secondary: 0 0% 96.5%;
    --secondary-foreground: 0 0% 9%;
    --muted: 0 0% 96.5%;
    --muted-foreground: 0 0% 45%;
    --accent: 0 0% 96.5%;
    --accent-foreground: 0 0% 9%;
    --destructive: 0 72% 51%;
    --destructive-foreground: 0 0% 98%;
    --success: 142 70% 32%;
    --warning: 35 90% 42%;
    --info: 217 91% 45%;
    --indigo: 217 91% 45%;
    --orange: 25 90% 48%;
    --purple: 263 65% 50%;
    --border: 0 0% 92%;
    --input: 0 0% 92%;
    --ring: 0 0% 9%;
    --radius: 0.5rem;

    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.04);
    --shadow-md: 0 1px 3px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.05);
    --shadow-lg: 0 10px 30px -10px rgb(0 0 0 / 0.15);
  }

  @media (prefers-color-scheme: dark) {
    :root, :root * {
      --background: 0 0% 7%;
      --foreground: 0 0% 95%;
      --card: 0 0% 9%;
      --card-foreground: 0 0% 95%;
      --popover: 0 0% 95%;
      --popover-foreground: 0 0% 9%;
      --primary: 0 0% 95%;
      --primary-foreground: 0 0% 9%;
      --secondary: 0 0% 14%;
      --secondary-foreground: 0 0% 95%;
      --muted: 0 0% 14%;
      --muted-foreground: 0 0% 60%;
      --accent: 0 0% 14%;
      --accent-foreground: 0 0% 95%;
      --destructive: 0 65% 55%;
      --destructive-foreground: 0 0% 95%;
      --success: 142 60% 45%;
      --warning: 35 85% 55%;
      --info: 217 85% 60%;
      --indigo: 217 85% 60%;
      --orange: 25 90% 60%;
      --purple: 263 70% 65%;
      --border: 0 0% 16%;
      --input: 0 0% 16%;
      --ring: 0 0% 80%;
    }
  }

  /* Typography — sadece Inter */
  body {
    font-family: 'Inter', system-ui, -apple-system, "Segoe UI", sans-serif !important;
    font-feature-settings: "cv11", "ss01" !important;
    background: hsl(var(--background)) !important;
    color: hsl(var(--foreground)) !important;
  }
  h1, h2, h3, .display, .panel-title {
    font-family: 'Inter', system-ui, sans-serif !important;
  }

  /* Navbar */
  .navbar {
    background: hsl(var(--background) / 0.85) !important;
    backdrop-filter: saturate(180%) blur(8px);
    -webkit-backdrop-filter: saturate(180%) blur(8px);
    border-bottom: 1px solid hsl(var(--border)) !important;
  }
  .navbar-inner {
    max-width: 1100px !important;
    padding: 14px 24px !important;
  }
  .brand {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    letter-spacing: -0.011em !important;
  }
  .brand-mark {
    width: 28px !important; height: 28px !important;
    border-radius: 7px !important;
    background: hsl(var(--foreground)) !important;
    color: hsl(var(--background)) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: -0.02em !important;
    box-shadow: none !important;
  }
  .brand-sub {
    color: hsl(var(--muted-foreground)) !important;
    font-weight: 400 !important;
    font-size: 13px !important;
  }

  /* Tabs — minimal underline */
  .tabs {
    max-width: 1100px !important;
    padding: 0 16px !important;
    gap: 2px !important;
    border-top: none !important;
  }
  .tab {
    height: 42px !important;
    padding: 0 14px !important;
    border-radius: 0 !important;
    background: transparent !important;
    color: hsl(var(--muted-foreground)) !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    border: 0 !important;
    border-bottom: 1.5px solid transparent !important;
    transition: color 0.15s, border-color 0.15s !important;
  }
  .tab:hover {
    background: transparent !important;
    color: hsl(var(--foreground)) !important;
  }
  .tab.active {
    background: transparent !important;
    color: hsl(var(--foreground)) !important;
    border-bottom-color: hsl(var(--foreground)) !important;
    font-weight: 600 !important;
  }
  .tab.active .count {
    background: hsl(var(--foreground)) !important;
    color: hsl(var(--background)) !important;
  }
  .tab .count {
    background: hsl(var(--secondary)) !important;
    color: hsl(var(--muted-foreground)) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    padding: 1px 7px !important;
    border-radius: 999px !important;
  }

  /* Main — daha kompakt genişlik */
  main {
    max-width: 880px !important;
    padding: 24px 20px !important;
  }
  @media (max-width: 640px) { main { padding: 16px !important; } }
  .navbar-inner { max-width: 880px !important; }
  .tabs { max-width: 880px !important; }

  .panel-title {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: hsl(var(--muted-foreground)) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    margin: 4px 0 16px !important;
  }

  /* ============ Standart responsive grid (bento yok, agresif reset) ============ */
  .exercise-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)) !important;
    gap: 10px !important;
    grid-auto-rows: auto !important;
    align-items: start !important;
  }
  /* Tüm bento data-id selectorlarını sıfırla, kart içeriği taşmasın */
  .ex-card,
  .ex-card[data-id],
  .ex-card[data-id*="kelime"],
  .ex-card[data-id*="cumle"],
  .ex-card[data-id*="cümle"],
  .ex-card[data-id*="paragraf"],
  .ex-card[data-id*="tekerleme"],
  .ex-card[data-id*="kelime-yt"],
  .ex-card[data-id*="tekerleme-"] {
    grid-column: span 1 !important;
    grid-row: span 1 !important;
    min-height: 90px !important;
    height: auto !important;
    max-height: none !important;
    position: static !important;
    transform: none !important;
    overflow: hidden !important;
    word-wrap: break-word !important;
    overflow-wrap: anywhere !important;
  }
  .ex-card-text {
    overflow: hidden !important;
    word-wrap: break-word !important;
    overflow-wrap: anywhere !important;
    display: -webkit-box !important;
    -webkit-line-clamp: 4 !important;
    -webkit-box-orient: vertical !important;
  }
  .ex-card {
    background: hsl(var(--card)) !important;
    border: 1px solid hsl(var(--border)) !important;
    border-radius: var(--radius) !important;
    padding: 16px !important;
    box-shadow: none !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
  }
  .ex-card::after { display: none !important; }
  .ex-card:hover {
    border-color: hsl(var(--ring) / 0.5) !important;
    box-shadow: var(--shadow-sm) !important;
    transform: none !important;
  }
  .ex-card.active {
    border-color: hsl(var(--foreground)) !important;
    box-shadow: 0 0 0 1px hsl(var(--foreground)) !important;
  }
  .ex-card-text {
    font-family: 'Inter', sans-serif !important;
    font-size: 14.5px !important;
    font-weight: 500 !important;
    line-height: 1.5 !important;
    letter-spacing: -0.005em !important;
    color: hsl(var(--foreground)) !important;
  }
  .focus-tag {
    display: inline-flex !important;
    background: hsl(var(--secondary)) !important;
    color: hsl(var(--muted-foreground)) !important;
    border: 1px solid hsl(var(--border)) !important;
    border-radius: 4px !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    padding: 2px 7px !important;
    letter-spacing: 0 !important;
  }
  .difficulty span {
    width: 4px !important; height: 4px !important;
    background: hsl(var(--border)) !important;
  }
  .difficulty span.on { background: hsl(var(--foreground)) !important; }

  /* Recorder card */
  .card {
    background: hsl(var(--card)) !important;
    border: 1px solid hsl(var(--border)) !important;
    border-radius: var(--radius) !important;
    padding: 18px !important;
    box-shadow: none !important;
  }
  /* Recorder içindeki butonları yan yana sıkı tut */
  #recorder .row {
    display: flex !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    margin-top: 12px !important;
  }
  #recorder .row button {
    flex: 0 0 auto !important;
    white-space: nowrap !important;
  }
  @media (max-width: 480px) {
    #recorder .row button { flex: 1 1 auto !important; }
  }
  .target-display {
    font-family: 'Inter', sans-serif !important;
    font-size: 19px !important;
    line-height: 1.65 !important;
    font-weight: 400 !important;
    letter-spacing: -0.011em !important;
    padding: 18px 20px !important;
    background: hsl(var(--secondary) / 0.5) !important;
    border: 1px solid hsl(var(--border)) !important;
    border-radius: calc(var(--radius) - 2px) !important;
  }
  @media (max-width: 600px) {
    .target-display { font-size: 17px !important; padding: 14px 16px !important; }
  }

  /* Buttons — minimal, clean */
  button {
    height: 38px !important;
    padding: 0 14px !important;
    border-radius: calc(var(--radius) - 2px) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    letter-spacing: -0.005em !important;
    background: hsl(var(--card)) !important;
    color: hsl(var(--foreground)) !important;
    border: 1px solid hsl(var(--border)) !important;
    transition: background 0.12s, color 0.12s, border-color 0.12s !important;
    box-shadow: none !important;
  }
  button:hover:not(:disabled) {
    background: hsl(var(--secondary)) !important;
    transform: none !important;
    box-shadow: none !important;
  }
  button.primary {
    background: hsl(var(--foreground)) !important;
    color: hsl(var(--background)) !important;
    border-color: hsl(var(--foreground)) !important;
  }
  button.primary:hover:not(:disabled) {
    background: hsl(var(--foreground) / 0.88) !important;
    box-shadow: none !important;
  }
  button.danger {
    background: hsl(var(--destructive)) !important;
    color: white !important;
    border-color: hsl(var(--destructive)) !important;
  }
  button.danger:hover:not(:disabled) {
    background: hsl(var(--destructive) / 0.9) !important;
    box-shadow: none !important;
  }
  button.secondary {
    background: hsl(var(--card)) !important;
    border: 1px solid hsl(var(--border)) !important;
  }

  /* Word error markers — minimal underline */
  .word.error.kelime {
    background: transparent !important;
    color: hsl(var(--destructive)) !important;
    box-shadow: inset 0 -2px 0 hsl(var(--destructive)) !important;
  }
  .word.error.kritik_unsuz {
    background: transparent !important;
    color: hsl(var(--orange)) !important;
    box-shadow: inset 0 -2px 0 hsl(var(--orange)) !important;
  }
  .word.error.r_yutulmasi, .word.error.h_yutulmasi {
    background: transparent !important;
    color: hsl(var(--warning)) !important;
    box-shadow: inset 0 -2px 0 hsl(var(--warning)) !important;
  }
  .word.error.vurgu_yeri {
    background: transparent !important;
    color: hsl(var(--indigo)) !important;
    box-shadow: inset 0 -2px 0 hsl(var(--indigo)) !important;
  }
  .word-listen {
    width: 18px !important; height: 18px !important;
    background: hsl(var(--secondary)) !important;
    border: 1px solid hsl(var(--border)) !important;
    color: hsl(var(--muted-foreground)) !important;
    box-shadow: none !important;
  }
  .word-listen:hover {
    background: hsl(var(--foreground)) !important;
    color: hsl(var(--background)) !important;
    border-color: hsl(var(--foreground)) !important;
    transform: none !important;
  }
  .word-listen.playing {
    background: hsl(var(--success)) !important;
    color: white !important;
    border-color: hsl(var(--success)) !important;
  }

  /* Progress paneli — sade grid */
  .progress-panel {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 14px !important;
  }
  .progress-panel > .stat-grid {
    grid-column: auto !important;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)) !important;
    gap: 12px !important;
  }
  .progress-panel > .chart-card,
  .progress-panel > .chart-card:nth-of-type(2),
  .progress-panel > .chart-card:nth-of-type(3) {
    grid-column: auto !important;
  }
  .stat-card {
    background: hsl(var(--card)) !important;
    border: 1px solid hsl(var(--border)) !important;
    border-radius: var(--radius) !important;
    padding: 16px !important;
    box-shadow: none !important;
    overflow: hidden;
    position: relative;
  }
  .stat-card::before { display: none !important; }
  .stat-label {
    font-size: 11px !important;
    font-weight: 600 !important;
    color: hsl(var(--muted-foreground)) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
  }
  .stat-value {
    font-family: 'Inter', sans-serif !important;
    font-size: 26px !important;
    font-weight: 600 !important;
    letter-spacing: -0.025em !important;
    color: hsl(var(--foreground)) !important;
    margin-top: 6px !important;
    font-variant-numeric: tabular-nums !important;
  }
  .chart-card {
    background: hsl(var(--card)) !important;
    border: 1px solid hsl(var(--border)) !important;
    border-radius: var(--radius) !important;
    padding: 18px !important;
    box-shadow: none !important;
  }
  .chart-title {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: hsl(var(--foreground)) !important;
    text-transform: none !important;
    letter-spacing: -0.005em !important;
    margin-bottom: 12px !important;
  }
  .issue-bar-fill {
    background: hsl(var(--foreground)) !important;
  }
  .word-chip {
    background: hsl(var(--secondary)) !important;
    color: hsl(var(--foreground)) !important;
    border: 1px solid hsl(var(--border)) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 12px !important;
  }

  /* Video sözlüğü */
  .video-section {
    background: hsl(var(--card)) !important;
    border: 1px solid hsl(var(--border)) !important;
    border-radius: var(--radius) !important;
    padding: 20px !important;
    box-shadow: none !important;
    margin-bottom: 14px !important;
  }
  .video-header {
    padding-bottom: 14px !important;
    margin-bottom: 14px !important;
    border-bottom: 1px solid hsl(var(--border)) !important;
  }
  .video-header h3 {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    letter-spacing: -0.011em !important;
  }
  .video-link {
    background: hsl(var(--card)) !important;
    border: 1px solid hsl(var(--border)) !important;
    border-radius: calc(var(--radius) - 2px) !important;
    padding: 4px 10px !important;
    font-weight: 500 !important;
    color: hsl(var(--muted-foreground)) !important;
  }
  .video-link:hover {
    background: hsl(var(--secondary)) !important;
    color: hsl(var(--foreground)) !important;
  }

  /* Word practice cards — sade grid */
  .word-practice-card {
    background: hsl(var(--card)) !important;
    border: 1px solid hsl(var(--border)) !important;
    border-radius: calc(var(--radius) - 2px) !important;
    padding: 12px !important;
    box-shadow: none !important;
  }
  .word-practice-card:hover {
    border-color: hsl(var(--ring) / 0.5) !important;
    transform: none !important;
    box-shadow: var(--shadow-sm) !important;
  }
  .word-practice-card.expanded {
    border-color: hsl(var(--foreground)) !important;
    box-shadow: 0 0 0 1px hsl(var(--foreground)) !important;
  }
  .wp-text {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    letter-spacing: -0.011em !important;
  }
  .wp-btn {
    height: 30px !important;
    border-radius: calc(var(--radius) - 4px) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
  }
  .wp-btn.primary {
    background: hsl(var(--foreground)) !important;
    color: hsl(var(--background)) !important;
    border-color: hsl(var(--foreground)) !important;
  }
  .wp-btn.recording {
    background: hsl(var(--destructive)) !important;
    color: white !important;
    border-color: hsl(var(--destructive)) !important;
  }
  .wp-btn.playing {
    background: hsl(var(--success)) !important;
    color: white !important;
    border-color: hsl(var(--success)) !important;
  }
  .wp-pill {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 11px !important;
    background: hsl(var(--foreground)) !important;
    color: hsl(var(--background)) !important;
    padding: 2px 9px !important;
  }
  .wp-pill.mukemmel { background: hsl(var(--success)) !important; color: white !important; }
  .wp-pill.iyi { background: hsl(var(--info)) !important; color: white !important; }
  .wp-pill.gelistirilebilir { background: hsl(var(--warning)) !important; color: white !important; }
  .wp-pill.tekrar { background: hsl(var(--destructive)) !important; color: white !important; }

  /* Verdict */
  .verdict {
    font-family: 'Inter', sans-serif !important;
    font-size: 18px !important;
    font-weight: 600 !important;
    letter-spacing: -0.018em !important;
  }
  .score-pill {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    background: hsl(var(--foreground)) !important;
    color: hsl(var(--background)) !important;
    padding: 2px 10px !important;
    font-variant-numeric: tabular-nums !important;
  }

  /* Empty / placeholder */
  .empty, .placeholder {
    border: 1px dashed hsl(var(--border)) !important;
    border-radius: var(--radius) !important;
    background: transparent !important;
    color: hsl(var(--muted-foreground)) !important;
  }
  .placeholder-title {
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: hsl(var(--foreground)) !important;
    letter-spacing: -0.011em !important;
  }

  /* Tooltip */
  .tooltip {
    background: hsl(var(--popover)) !important;
    color: hsl(var(--popover-foreground)) !important;
    border: 1px solid hsl(var(--border)) !important;
    border-radius: calc(var(--radius) - 2px) !important;
    box-shadow: var(--shadow-md) !important;
    font-size: 13px !important;
  }
  .tooltip::before {
    background: hsl(var(--popover)) !important;
    border: 1px solid hsl(var(--border)) !important;
  }
  .tooltip b { color: inherit !important; }

  /* Recording dot */
  .recording-dot {
    background: hsl(var(--destructive)) !important;
  }

  /* Issue cards (wp-issue) - minimal */
  .wp-issue {
    background: hsl(var(--secondary) / 0.5) !important;
    border: 1px solid hsl(var(--border)) !important;
    border-left: 2px solid hsl(var(--foreground)) !important;
    border-radius: calc(var(--radius) - 4px) !important;
    color: hsl(var(--foreground)) !important;
  }
  .wp-issue:hover { background: hsl(var(--secondary)) !important; }
  .wp-issue.kelime { border-left-color: hsl(var(--destructive)) !important; }
  .wp-issue.kritik_unsuz { border-left-color: hsl(var(--orange)) !important; }
  .wp-issue.r_yutulmasi, .wp-issue.h_yutulmasi { border-left-color: hsl(var(--warning)) !important; }
  .wp-issue.vurgu_yeri { border-left-color: hsl(var(--indigo)) !important; }
  .wp-issue.dogallik { border-left-color: hsl(var(--purple)) !important; }
</style>
</head>'''

text = INDEX.read_text(encoding="utf-8")

# İlk </style>'ı bul (orijinal shadcn'in sonu).
first_style_end = text.find("</style>")
# Son </head>'i bul (önceki script bozmuş olabilir, üst üste </head></head>... olabilir).
last_head_close = text.rfind("</head>")
if first_style_end < 0 or last_head_close < 0:
    raise SystemExit("Style/head bulunamadı.")

# Aralıktaki herşeyi sil + yeni override yaz. CLEAN_OVERRIDE sonu </head> ile bitiyor.
# text[last_head_close + len("</head>"):] body'den itibaren olan kısım.
new_text = (
    text[: first_style_end + len("</style>")]
    + CLEAN_OVERRIDE  # bu zaten </head> ile bitiyor
    + text[last_head_close + len("</head>"):]
)

INDEX.write_text(new_text, encoding="utf-8")
old_size = len(text)
new_size = len(new_text)
print(f"index.html: {old_size} -> {new_size} byte ({old_size - new_size:+d})")
print("BENTO override silindi, Clean SaaS override eklendi.")
