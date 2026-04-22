# 🌍 Eco-Climate Intelligence
### A Multi-Sectoral Climate Decision Support System

> **Department of AI & Data Science · CMRIT, Bengaluru**  
> Authors: K Siddharth · Shivani Sundareswaran · Rabiya Khanum  
> Guide: Mr. Abdul Jabbar K

---

## 📦 Project Structure

```
eco_climate_intelligence/
│
├── app.py                        ← Main Streamlit application (run this)
├── requirements.txt              ← All Python dependencies
│
└── modules/
    ├── __init__.py
    ├── translations.py           ← 11-language support (EN + 10 Indian)
    ├── data_fetcher.py           ← Geocoding + Meteostat API integration
    ├── agriculture.py            ← GDD, sowing calendar, frost risk
    ├── water.py                  ← SPI, drought/flood risk, rainfall trends
    ├── disaster.py               ← Heat/cold waves, storm events, risk map
    ├── urban.py                  ← UHI intensity, diurnal range, heat-island map
    ├── energy.py                 ← HDD/CDD, grid stress, renewable potential
    └── climate_research.py       ← Warming trend, anomaly detection, regression
```

---

## ⚙️ Step-by-Step Setup

### Step 1 — Install Python 3.10+

Make sure you have Python 3.10 or higher:
```bash
python --version
```
If not installed, download from https://python.org/downloads

---

### Step 2 — Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3 — Install all dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` — interactive web dashboard
- `meteostat` — 3-year historical + live climate data
- `geopy` — city name → lat/lon geocoding
- `folium` + `streamlit-folium` — interactive maps
- `pandas`, `numpy`, `scipy` — data processing
- `plotly` — beautiful interactive charts

---

### Step 4 — Run the app

```bash
streamlit run app.py
```

The browser will open automatically at `http://localhost:8501`

---

## 🚀 How to Use

1. **Select Language** from the dropdown in the left sidebar (11 options)
2. **Type any city name** (e.g., `Bengaluru`, `Mumbai`, `Delhi`, `Chennai`)
3. Click **"⚡ Fetch Climate Data"** — waits ~5–10 seconds for API
4. **Choose a module** from the sidebar radio buttons:
   - 🌾 Agriculture — crop suitability, GDD, sowing calendar
   - 💧 Water — SPI drought index, flood risk, rainfall trends
   - 🚨 Disaster — heat/cold waves, storm days, risk zone map
   - 🏙️ Urban — UHI intensity, heat island visualisation
   - ⚡ Energy — HDD/CDD, grid stress gauge, renewables
   - 🔬 Climate — warming trend, anomaly analysis, regression

---

## 📶 Low-Bandwidth Mode

Toggle **"📶 Low-Bandwidth Mode"** in the sidebar to:
- Disable all maps and heavy charts
- Show only a lightweight data table
- Enable CSV download for offline analysis

Ideal for rural areas or limited connectivity.

---

## 🌐 Supported Languages

| Language  | Language  | Language  | Language  |
|-----------|-----------|-----------|-----------|
| 🇬🇧 English | 🇮🇳 Hindi | 🇮🇳 Tamil | 🇮🇳 Telugu |
| 🇮🇳 Kannada | 🇮🇳 Malayalam | 🇮🇳 Bengali | 🇮🇳 Marathi |
| 🇮🇳 Gujarati | 🇮🇳 Punjabi | 🇮🇳 Odia | |

---

## 🧠 Key Technical Concepts

| Metric | Formula | Used In |
|--------|---------|---------|
| **GDD** | max(0, (Tmax+Tmin)/2 − Base_temp) | Agriculture |
| **SPI-3** | (rolling_rain − mean) / std | Water |
| **HDD** | max(0, 18 − Tavg) | Energy |
| **CDD** | max(0, Tavg − 18) | Energy |
| **UHI** | Δ(diurnal range) vs long-term mean | Urban |
| **Warming Rate** | Linear regression slope × 10 yrs | Climate |

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| "No station found" error | Try a bigger nearby city (e.g., state capital) |
| App won't start | Check `pip install -r requirements.txt` succeeded |
| Slow data fetch | Normal — API pulls 1000+ daily records. First run caches. |
| Maps not showing | Ensure `streamlit-folium` is installed correctly |
| Import errors | Verify you're running from inside the project folder |

---

## 📚 References

- Meteostat Python Library: https://dev.meteostat.net/python/
- Geopy Documentation: https://geopy.readthedocs.io/
- Folium Documentation: https://python-visualization.github.io/folium/
- Streamlit Documentation: https://docs.streamlit.io/
- IMD Heat Wave Criteria: https://mausam.imd.gov.in/
