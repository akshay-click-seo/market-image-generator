# Market Image Generator

Automation tool jo market-research dashboard images generate karta hai — Market Growth (bar chart + stats), Regional Analysis (world map highlight), aur Segmentation (donut chart) — "Informes de Expertos" jaisi visual style mein.

## Setup (local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Browser mein `http://localhost:8501` khulega.

Standalone test suite chalane ke liye (bina UI ke, sab pages/buttons verify karta hai):

```bash
python3 test_app.py
```

## Deploy free pe (Streamlit Community Cloud)

1. Is folder ka code ek GitHub repo mein daalein (public repo, e.g. `market-image-generator`)
2. [share.streamlit.io](https://share.streamlit.io) pe GitHub se sign in karein
3. "New app" → apna repo + branch `main` + main file `app.py` select karein → Deploy
4. 1-2 minute mein public URL mil jayega (`your-app.streamlit.app`)

`requirements.txt` intentionally sirf 4 lightweight libraries (streamlit, pillow, matplotlib, numpy) rakhta hai taaki free-tier deploy fast aur reliable ho — koi system-level dependency (GDAL, cairo, etc.) nahi chahiye.

## Features

- **Dashboard** — overview aur quick navigation
- **Market Growth** — bar chart + CAGR/market-size stat cards; 2 styles (full stat-card layout ya minimal world-map layout); manual fields ya "Auto Fetch" paste box (regex se IMARC/IDE paragraph se data extract karta hai, no internet/AI needed)
- **Regional Analysis** — world map jisme selected country automatically highlight + pin + flag badge ke saath
- **Segmentation** — 2 se 6 segments ka donut chart, auto colors/connector lines
- **Settings** — background style, fonts (Poppins bundled + custom TTF upload), logo, website, image size (presets ya custom)
- **Export** — PNG / WEBP / JPG / PDF, quality 50-100%

## Folder Structure

```
market-image-generator/
├── app.py                  # Main Streamlit app shell (nav: Dashboard/Growth/Regional/Segmentation/Settings/Export)
├── requirements.txt
├── test_app.py              # Headless smoke tests (Streamlit AppTest)
├── assets/
│   ├── world_countries.geojson   # Natural Earth country boundaries (110m)
│   ├── fonts/                    # Bundled Poppins family + custom/ uploads
│   └── _map_cache/               # Auto-generated map render cache
├── sections/                # Streamlit page modules (named `sections/` not `pages/`
│   │                         # because Streamlit reserves `pages/` for its own
│   │                         # automatic multi-page routing)
│   ├── growth.py
│   ├── regional.py
│   └── segmentation.py
├── utils/
│   ├── parser.py             # Regex-based auto-extraction from pasted report text
│   ├── chart.py               # Bar chart + donut chart rendering (matplotlib)
│   ├── map.py                  # World map rendering + country highlight/pin (geojson + matplotlib)
│   ├── fonts.py                 # Font management (bundled + custom upload)
│   ├── export.py                 # PNG/WEBP/JPG/PDF export
│   ├── backgrounds.py             # Background presets (Classic Blue/Modern White/Gradient/Light/Dark/Custom)
│   ├── icons.py                    # Programmatically-drawn stat-card icons
│   └── state.py                     # Shared Streamlit session-state defaults
└── templates/
    ├── growth_style1.py    # Full bar chart + right-side stat card column
    ├── growth_style2.py    # Minimal layout: left CAGR card + world map watermark
    ├── regional_style.py   # World map + country highlight + stat cards
    └── segmentation_style.py  # Donut chart + connector-line labels
```

## Notes on implementation choices

- **AI parsing**: Regex-only (Python's built-in `re` module), no external API key needed — works fully offline. Handles English and Spanish report sentence patterns (e.g. "reached USD X Million in YEAR ... CAGR of Y% during A-B" / "alcanzó ... USD X Mil Millones en YEAR ... CAGR del Y%").
- **World map**: Rendered from a bundled Natural Earth GeoJSON (110m resolution, ~800KB) using matplotlib — no live network calls needed at runtime, and no geopandas/GDAL dependency. Country highlighting works by name or ISO code lookup.
- **Fonts**: Poppins (Regular/Medium/Bold) is bundled directly under `assets/fonts/` for full offline operation. Upload any custom TTF/OTF via Settings.
- **Export**: Pillow handles PNG/WEBP/JPG/PDF at any custom canvas size and quality 50-100%.
- **Dependencies kept minimal on purpose**: only streamlit, pillow, matplotlib, numpy — everything else (geopandas, opencv, cairosvg, pandas, plotly, python-docx) was in the original spec but never actually used by the implementation, so it was trimmed for a faster, more reliable deploy.
