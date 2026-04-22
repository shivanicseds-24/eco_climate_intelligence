"""
╔══════════════════════════════════════════════════════════════╗
║         ECO-CLIMATE INTELLIGENCE                             ║
║         A Multi-Sectoral Decision Support System             ║
║                                                              ║
║   Authors  : K Siddharth · Shivani Sundareswaran             ║
║              Rabiya Khanum                                   ║
║   Guide    : Mr. Abdul Jabbar K                              ║
║   Dept     : AI & Data Science, CBIT                         ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# ── Page config — must be first Streamlit call ──────────────────
st.set_page_config(
    page_title="Eco-Climate Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Local imports ───────────────────────────────────────────────
from modules.translations import LANGUAGES, t
from modules.data_fetcher  import get_coordinates, fetch_weather_data, latest_conditions
from modules               import agriculture, water, disaster, urban, energy, climate_research

# ══════════════════════════════════════════════════════════════════
# GLOBAL CSS — one clean import, no repeated inline blobs
# ══════════════════════════════════════════════════════════════════
st.markdown(
    """
    <style>
    /* ── Fonts & Base ─────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background: #f1f5f9;
    }

    /* ── Sidebar ───────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: none;
    }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stTextInput input {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] .stSelectbox select,
    [data-testid="stSidebar"] .stSelectbox > div {
        background: #1e293b !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] .stButton button {
        background: linear-gradient(135deg, #028090, #02c39a) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
        padding: 10px !important;
        font-size: 0.95rem !important;
        transition: opacity 0.2s !important;
    }
    [data-testid="stSidebar"] .stButton button:hover { opacity: 0.88 !important; }

    /* ── Main area ─────────────────────────────────────────────── */
    [data-testid="block-container"] { padding: 1.2rem 1.6rem 2rem; }

    /* ── Tabs ──────────────────────────────────────────────────── */
    div[data-testid="stTabs"] button {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        border-radius: 6px 6px 0 0 !important;
        padding: 8px 18px !important;
        color: #64748b !important;
        border: none !important;
        background: transparent !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #028090 !important;
        border-bottom: 3px solid #028090 !important;
        background: white !important;
    }

    /* ── Metric cards  ─────────────────────────────────────────── */
    [data-testid="metric-container"] {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }

    /* ── Dataframes ────────────────────────────────────────────── */
    [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

    /* ── Plotly charts ─────────────────────────────────────────── */
    .js-plotly-plot { border-radius: 10px; }

    /* ── Hide default Streamlit chrome ─────────────────────────── */
    #MainMenu, footer, header { visibility: hidden; }


    /* ── Scrollbar ─────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f1f5f9; }
    ::-webkit-scrollbar-thumb { background: #94a3b8; border-radius: 3px; }

    /* ── Folium map iframe ─────────────────────────────────────── */
    iframe { border-radius: 10px; }

    /* ── Low-bandwidth notice ──────────────────────────────────── */
    .bw-notice {
        background: #fffbeb; border-left: 4px solid #f59e0b;
        border-radius: 6px; padding: 10px 14px;
        font-size: 0.82rem; color: #92400e; margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        # Logo / brand
        st.markdown(
            """
            <div style="text-align:center;padding:20px 10px 8px;">
              <div style="font-size:2.4rem;">🌍</div>
              <div style="font-family:'Space Grotesk',sans-serif;font-size:1.15rem;
                          font-weight:700;color:#f1f5f9;letter-spacing:-0.3px;">
                Eco-Climate Intelligence
              </div>
              <div style="font-size:0.72rem;color:#94a3b8;margin-top:3px;letter-spacing:0.4px;
                          text-transform:uppercase;">
                Multi-Sectoral Decision Support
              </div>
            </div>
            <hr style="border:none;border-top:1px solid #334155;margin:12px 0;">
            """,
            unsafe_allow_html=True,
        )

        # Language selector
        lang_display = st.selectbox(
            "🌐 Language",
            options=list(LANGUAGES.keys()),
            index=0,
            key="lang_select",
        )
        lang = LANGUAGES[lang_display]

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # City search
        st.markdown(
            f"<div style='font-size:0.8rem;color:#94a3b8;text-transform:uppercase;"
            f"letter-spacing:0.5px;margin-bottom:4px;'>{t('search_city', lang)}</div>",
            unsafe_allow_html=True,
        )
        city_input = st.text_input(
            label="city_input_hidden",
            placeholder=t("enter_city", lang),
            label_visibility="collapsed",
            key="city_input",
        )
        fetch_clicked = st.button(t("fetch_data", lang), key="fetch_btn")

        # Low bandwidth mode
        st.markdown("<hr style='border:none;border-top:1px solid #334155;margin:14px 0;'>", unsafe_allow_html=True)
        low_bw = st.toggle("📶 Low-Bandwidth Mode", value=False, key="low_bw")
        if low_bw:
            st.markdown(
                "<div class='bw-notice' style='background:#1e293b;border-color:#f59e0b;color:#fde68a;'>"
                "Maps and heavy charts are disabled. Data tables will be shown instead.</div>",
                unsafe_allow_html=True,
            )

        # Module selector
        st.markdown("<hr style='border:none;border-top:1px solid #334155;margin:14px 0;'>", unsafe_allow_html=True)
        module_labels = [
            t("agriculture", lang),
            t("water",       lang),
            t("disaster",    lang),
            t("urban",       lang),
            t("energy",      lang),
            t("climate",     lang),
        ]
        active_module = st.radio(
            t("select_module", lang),
            options=module_labels,
            key="module_radio",
        )

        # Data attribution footer
        st.markdown(
            """
            <hr style='border:none;border-top:1px solid #334155;margin:14px 0;'>
            <div style='font-size:0.7rem;color:#475569;text-align:center;line-height:1.5;'>
              📡 Meteostat API &nbsp;|&nbsp; 🌐 Nominatim Geocoder<br>
              Dept. of AI & DS · CBIT, Bengaluru
            </div>
            """,
            unsafe_allow_html=True,
        )

    return lang, city_input, fetch_clicked, low_bw, active_module, module_labels


# ══════════════════════════════════════════════════════════════════
# HEADER BANNER (shown after data is loaded)
# ══════════════════════════════════════════════════════════════════
def render_data_header(city_display: str, lat: float, lon: float,
                       df: pd.DataFrame, lang: str):
    cond = latest_conditions(df)
    col_city, col_t1, col_t2, col_t3, col_t4 = st.columns([2.5, 1, 1, 1, 1])

    with col_city:
        st.markdown(
            f"""<div style="background:linear-gradient(135deg,#028090,#02c39a);
                            color:white;border-radius:12px;padding:14px 18px;">
                  <div style="font-size:0.72rem;opacity:0.8;text-transform:uppercase;
                               letter-spacing:0.5px;">{t('city_label',lang)}</div>
                  <div style="font-size:1.6rem;font-weight:700;letter-spacing:-0.5px;">
                    {city_display}
                  </div>
                  <div style="font-size:0.75rem;opacity:0.75;margin-top:2px;">
                    {lat}°N, {lon}°E &nbsp;·&nbsp; {t('data_source',lang)}
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )

    cards = [
        (f"{cond.get('avg_temp', '—')}°C", t("current_temp", lang), "7-day avg",  "#f97316"),
        (f"{cond.get('max_temp', '—')}°C", t("max_temp",     lang), "7-day high", "#ef4444"),
        (f"{cond.get('min_temp', '—')}°C", t("min_temp",     lang), "7-day low",  "#3b82f6"),
        (f"{cond.get('total_prcp','—')} mm", t("avg_rainfall", lang),"7-day total","#0ea5e9"),
    ]
    for col, (val, label, sub, color) in zip([col_t1, col_t2, col_t3, col_t4], cards):
        with col:
            st.markdown(
                f"""<div style="background:#1e293b;border-radius:12px;padding:14px;
                                text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.06);
                                border-top:3px solid {color};height:100%;">
                      <div style="font-size:1.5rem;font-weight:700;color:#f1f5f9;">{val}</div>
                      <div style="font-size:0.68rem;color:#94a3b8;text-transform:uppercase;
                                   letter-spacing:0.4px;margin-top:2px;">{label}</div>
                      <div style="font-size:0.65rem;color:#64748b;">{sub}</div>
                    </div>""",
                unsafe_allow_html=True,
            )

    # Data coverage bar
    start_date = df.index[0].strftime("%b %Y")
    end_date   = df.index[-1].strftime("%b %Y")
    n_days     = len(df)
    st.markdown(
        f"""<div style="background:#1e293b;border-radius:8px;padding:8px 16px;margin-top:10px;
                        font-size:0.78rem;color:#000000;display:flex;justify-content:space-between;">
              <span>📅 <strong>{t('year_range',lang)}:</strong> {start_date} → {end_date}</span>
              <span>📊 <strong>{n_days:,} daily records</strong></span>
              <span>🕒 Updated: {datetime.now().strftime('%d %b %Y, %H:%M')}</span>
            </div>""",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
# WELCOME SCREEN (no city entered yet)
# ══════════════════════════════════════════════════════════════════
def render_welcome(lang: str):
    st.markdown(
        f"""
        <div style="text-align:center;padding:60px 20px 40px;">
          <div style="font-size:4rem;">🌍</div>
          <h1 style="font-family:'Space Grotesk',sans-serif;font-size:2.2rem;
                     font-weight:700;color:#0f172a;margin:12px 0 8px;">
            {t('welcome', lang)}
          </h1>
          <p style="color:#64748b;font-size:1rem;max-width:600px;margin:0 auto 32px;line-height:1.7;">
            {t('welcome_desc', lang)}
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature grid
    features = [
        ("🌾", t("agriculture", lang), "GDD · Sowing Calendar · Frost Risk · Crop Stress"),
        ("💧", t("water",       lang), "SPI · Drought Index · Flood Detection · Seasonal Analysis"),
        ("🚨", t("disaster",    lang), "Heat Waves · Cold Waves · Storm Days · Risk Map"),
        ("🏙️", t("urban",       lang), "UHI Intensity · Diurnal Range · Heat Island Map"),
        ("⚡", t("energy",      lang), "HDD/CDD · Grid Stress · Solar & Wind Potential"),
        ("🔬", t("climate",     lang), "Warming Trend · Anomaly Detection · Regression Analysis"),
    ]
    cols = st.columns(3)
    for i, (icon, name, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(
                f"""<div style="background:white;border-radius:14px;padding:22px 18px;
                                box-shadow:0 2px 12px rgba(0,0,0,0.07);margin-bottom:14px;
                                border-top:4px solid #028090;transition:transform 0.2s;">
                      <div style="font-size:1.8rem;margin-bottom:10px;">{icon}</div>
                      <div style="font-family:'Space Grotesk',sans-serif;font-size:1rem;
                                   font-weight:600;color:#0f172a;margin-bottom:6px;">{name}</div>
                      <div style="font-size:0.78rem;color:#64748b;line-height:1.5;">{desc}</div>
                    </div>""",
                unsafe_allow_html=True,
            )

    # How it works
    st.markdown(
        """
        <div style="background:white;border-radius:14px;padding:24px 28px;
                    box-shadow:0 2px 12px rgba(0,0,0,0.07);margin-top:8px;">
          <h3 style="font-family:'Space Grotesk',sans-serif;font-size:1.05rem;
                     font-weight:700;color:#0f172a;margin-bottom:14px;">
            How it works
          </h3>
          <div style="display:flex;gap:20px;flex-wrap:wrap;">
            <div style="flex:1;min-width:140px;text-align:center;padding:12px;">
              <div style="font-size:1.6rem;">1️⃣</div>
              <div style="font-weight:600;color:#0f172a;font-size:0.88rem;margin:6px 0 4px;">Enter City</div>
              <div style="font-size:0.77rem;color:#64748b;">Any city worldwide — geocoded via OpenStreetMap</div>
            </div>
            <div style="flex:1;min-width:140px;text-align:center;padding:12px;">
              <div style="font-size:1.6rem;">2️⃣</div>
              <div style="font-weight:600;color:#0f172a;font-size:0.88rem;margin:6px 0 4px;">Fetch Data</div>
              <div style="font-size:0.77rem;color:#64748b;">3 years of verified daily weather from Meteostat</div>
            </div>
            <div style="flex:1;min-width:140px;text-align:center;padding:12px;">
              <div style="font-size:1.6rem;">3️⃣</div>
              <div style="font-weight:600;color:#0f172a;font-size:0.88rem;margin:6px 0 4px;">Pick a Module</div>
              <div style="font-size:0.77rem;color:#64748b;">Select your sector from the sidebar menu</div>
            </div>
            <div style="flex:1;min-width:140px;text-align:center;padding:12px;">
              <div style="font-size:1.6rem;">4️⃣</div>
              <div style="font-weight:600;color:#0f172a;font-size:0.88rem;margin:6px 0 4px;">Get Insights</div>
              <div style="font-size:0.77rem;color:#64748b;">Actionable metrics, charts, maps, recommendations</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
# LOW-BANDWIDTH SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════
def render_low_bw_summary(df: pd.DataFrame, city: str, lang: str):
    st.markdown(
        f"""<div class="bw-notice">
          📶 Low-Bandwidth Mode: showing data tables only. Toggle off in sidebar for full charts & maps.
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown(f"#### 📊 3-Year Monthly Summary — {city}")
    monthly = df.groupby(["year", "month"]).agg(
        Avg_Temp_C=("tavg", "mean"),
        Max_Temp_C=("tmax", "mean"),
        Min_Temp_C=("tmin", "mean"),
        Rain_mm   =("prcp", "sum"),
    ).round(1).reset_index()
    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                   7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    monthly["Month"] = monthly["month"].map(month_names)
    display = monthly[["year", "Month", "Avg_Temp_C", "Max_Temp_C", "Min_Temp_C", "Rain_mm"]]
    display.columns = ["Year", "Month", "Avg Temp (°C)", "Max Temp (°C)", "Min Temp (°C)", "Rain (mm)"]
    st.dataframe(display, use_container_width=True, hide_index=True, height=450)

    csv = display.to_csv(index=False).encode()
    st.download_button("⬇️ Download CSV", csv, "eco_climate_data.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    lang, city_input, fetch_clicked, low_bw, active_module, module_labels = render_sidebar()

    # ── Persist state across reruns
    if "df" not in st.session_state:
        st.session_state["df"]           = None
        st.session_state["city_display"] = ""
        st.session_state["lat"]          = None
        st.session_state["lon"]          = None

    # ── Trigger data fetch
    if fetch_clicked and city_input.strip():
        with st.spinner(t("loading", lang)):
            lat, lon, city_display = get_coordinates(city_input.strip())
            if lat is None:
                st.error("❌ Could not geocode that city. Try a major city or check spelling.")
                st.stop()
            df = fetch_weather_data(lat, lon)
            if df is None:
                st.error(t("no_data", lang))
                st.stop()
            st.session_state["df"]           = df
            st.session_state["city_display"] = city_display
            st.session_state["lat"]          = lat
            st.session_state["lon"]          = lon

    df           = st.session_state["df"]
    city_display = st.session_state["city_display"]
    lat          = st.session_state["lat"]
    lon          = st.session_state["lon"]

    # ── No data yet
    if df is None:
        render_welcome(lang)
        return

    # ── Data header strip
    render_data_header(city_display, lat, lon, df, lang)
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # ── Low-bandwidth override
    if low_bw:
        render_low_bw_summary(df, city_display, lang)
        return

    # ── Module routing
    module_map = {
        module_labels[0]: lambda: agriculture.render(df, city_display, lat, lon, lang),
        module_labels[1]: lambda: water.render(df, city_display, lat, lon, lang),
        module_labels[2]: lambda: disaster.render(df, city_display, lat, lon, lang),
        module_labels[3]: lambda: urban.render(df, city_display, lat, lon, lang),
        module_labels[4]: lambda: energy.render(df, city_display, lat, lon, lang),
        module_labels[5]: lambda: climate_research.render(df, city_display, lat, lon, lang),
    }

    renderer = module_map.get(active_module)
    if renderer:
        renderer()
    else:
        st.info("Select a module from the sidebar.")


if __name__ == "__main__":
    main()
