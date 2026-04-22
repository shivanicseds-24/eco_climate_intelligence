"""
Agriculture Module — Eco-Climate Intelligence
Computes Growing Degree Days (GDD), frost risk, sowing recommendations,
and crop stress indices from historical daily weather data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from modules.translations import t

# ── GDD base temps for common Indian crops (°C)
CROP_BASE_TEMPS = {
    "Rice (Paddy)": 10, "Wheat": 0, "Maize (Corn)": 10,
    "Cotton": 15, "Soybean": 10, "Sugarcane": 15,
    "Sunflower": 6, "Groundnut": 14, "Chickpea": 0, "Lentil": 0,
}

# ── Simplified kharif/rabi crop calendar for India
SOWING_CALENDAR = {
    range(6, 9): {   # June–August: Kharif season
        "crops": ["Rice (Paddy)", "Maize (Corn)", "Cotton", "Soybean", "Groundnut"],
        "season": "Kharif",
        "note": "Monsoon onset — ideal for water-intensive crops.",
    },
    range(10, 13): {  # Oct–December: Rabi season
        "crops": ["Wheat", "Chickpea", "Lentil", "Sunflower"],
        "season": "Rabi",
        "note": "Post-monsoon cooling — sow winter staples now.",
    },
    range(2, 5): {   # Feb–April: Zaid/Summer
        "crops": ["Sunflower", "Maize (Corn)", "Groundnut"],
        "season": "Zaid (Summer)",
        "note": "Short summer season — focus on fast-maturing varieties.",
    },
}


def _gdd_series(df: pd.DataFrame, base: float) -> pd.Series:
    """
    GDD per day = max(0, (tmax + tmin) / 2 − base_temp).
    Negative values are clipped to zero — cold days contribute nothing.
    """
    mean_temp = (df["tmax"] + df["tmin"]) / 2
    return np.maximum(0, mean_temp - base)


def _frost_days(df: pd.DataFrame) -> int:
    """Days where the minimum temperature drops below 0°C."""
    return int((df["tmin"] < 0).sum())


def _current_season_gdd(df: pd.DataFrame, base: float = 10) -> float:
    """Accumulated GDD from Jan 1 of the current year."""
    this_year = df[df["year"] == df["year"].max()]
    return float(_gdd_series(this_year, base).sum())


def _get_sowing_rec(month: int) -> dict:
    for month_range, info in SOWING_CALENDAR.items():
        if month in month_range:
            return info
    return {
        "crops": ["Check local guidelines"],
        "season": "Transition",
        "note": "This is typically an inter-season period. Consult your local agricultural extension office.",
    }


def _monthly_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily data to monthly averages for charting."""
    return (
        df.groupby(["year", "month"])
        .agg(tavg=("tavg", "mean"), tmax=("tmax", "mean"),
             tmin=("tmin", "mean"), prcp=("prcp", "sum"))
        .reset_index()
    )


def _metric_card(value, label, color="#028090", unit="", sub=""):
    st.markdown(
        f"""
        <div style="background:white;border-radius:12px;padding:18px 14px;text-align:center;
                    box-shadow:0 2px 10px rgba(0,0,0,0.07);border-top:4px solid {color};">
            <div style="font-size:1.9rem;font-weight:700;color:#1e293b;">{value}<span style="font-size:1rem;color:#64748b;">{unit}</span></div>
            <div style="font-size:0.75rem;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:0.5px;">{label}</div>
            {"<div style='font-size:0.7rem;color:#94a3b8;margin-top:2px;'>"+sub+"</div>" if sub else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(df: pd.DataFrame, city: str, lat: float, lon: float, lang: str):
    current_month = df.index[-1].month

    # ── KPI calculations
    gdd_ytd      = _current_season_gdd(df)
    frost_days   = _frost_days(df)
    total_rain   = round(df["prcp"].sum(), 0)
    avg_temp_7d  = round(df["tavg"].tail(7).mean(), 1)
    max_temp_7d  = round(df["tmax"].tail(7).max(), 1)

    sowing       = _get_sowing_rec(current_month)
    frost_risk   = "High" if avg_temp_7d < 5 else "Low"

    # ── Section header
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#1e6b2e,#4caf50);
                        color:white;padding:18px 22px;border-radius:12px;margin-bottom:18px;">
              <h2 style="margin:0;font-size:1.4rem;">🌾 {t('agriculture',lang)}</h2>
              <p style="margin:4px 0 0;opacity:0.85;font-size:0.85rem;">{t('city_label',lang)}: <strong>{city}</strong></p>
            </div>""",
        unsafe_allow_html=True,
    )

    # ── Metric row 1
    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric_card(f"{avg_temp_7d}", t("current_temp", lang), "#028090", "°C", "7-day avg")
    with c2: _metric_card(f"{int(gdd_ytd)}", t("gdd", lang), "#22c55e", " GDD", "base 10°C, YTD")
    with c3: _metric_card(f"{int(total_rain)}", t("total_rain", lang), "#0ea5e9", " mm", "3-year total")
    with c4: _metric_card(f"{frost_days}", t("frost_days", lang), "#6366f1", " days", "tmin < 0°C")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f"<p style='color:#1e293b;font-weight:600;font-size:0.95rem;margin-bottom:4px;'>📈 {t('monthly_temp', lang)}</p>", unsafe_allow_html=True)
        monthly = _monthly_stats(df)
        monthly["date_label"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly["date_label"], y=monthly["tmax"],
            name="Max Temp", line=dict(color="#ef4444", width=1.5),
            fill=None, mode="lines",
        ))
        fig.add_trace(go.Scatter(
            x=monthly["date_label"], y=monthly["tavg"],
            name="Avg Temp", line=dict(color="#f97316", width=2),
            fill="tonexty", fillcolor="rgba(249,115,22,0.08)", mode="lines",
        ))
        fig.add_trace(go.Scatter(
            x=monthly["date_label"], y=monthly["tmin"],
            name="Min Temp", line=dict(color="#3b82f6", width=1.5),
            fill="tonexty", fillcolor="rgba(59,130,246,0.06)", mode="lines",
        ))
        fig.add_hline(y=10, line_dash="dot", line_color="#22c55e",
                      annotation_text="GDD base (10°C)", annotation_position="bottom right")
        fig.update_layout(
            template="plotly_dark", height=280, margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            yaxis_title="°C", xaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown(f"<p style='color:#1e293b;font-weight:600;font-size:0.95rem;margin-bottom:4px;'>🌧️ {t('monthly_rain', lang)}</p>", unsafe_allow_html=True)
        monthly_rain = df.groupby(["year", "month"])["prcp"].sum().reset_index()
        monthly_rain["date_label"] = (
            monthly_rain["year"].astype(str) + "-" + monthly_rain["month"].astype(str).str.zfill(2)
        )

        fig2 = go.Figure(go.Bar(
            x=monthly_rain["date_label"],
            y=monthly_rain["prcp"],
            marker_color=[
                "#0ea5e9" if v < 100 else "#0369a1" if v < 200 else "#1e3a8a"
                for v in monthly_rain["prcp"]
            ],
            hovertemplate="%{x}: %{y:.0f} mm<extra></extra>",
        ))
        fig2.add_hline(y=100, line_dash="dash", line_color="#f59e0b",
                       annotation_text="100mm threshold", annotation_position="top right")
        fig2.update_layout(
            template="plotly_dark", height=280, margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title="mm", xaxis_title="",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── GDD accumulation chart (full year view)
    st.markdown(f"<p style='color:#1e293b;font-weight:600;font-size:0.95rem;margin-bottom:4px;'>🌱 Growing Degree Day Accumulation (Current Year)</p>", unsafe_allow_html=True)
    this_year_df = df[df["year"] == df["year"].max()].copy()
    this_year_df["gdd_daily"]  = _gdd_series(this_year_df, base=10)
    this_year_df["gdd_cumsum"] = this_year_df["gdd_daily"].cumsum()

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=this_year_df.index, y=this_year_df["gdd_cumsum"],
        fill="tozeroy", fillcolor="rgba(34,197,94,0.15)",
        line=dict(color="#16a34a", width=2.5),
        name="Cumulative GDD",
        hovertemplate="%{x|%b %d}: %{y:.0f} GDD<extra></extra>",
    ))
    # Horizontal reference lines for major crops
    for crop, base in [("Wheat", 1200), ("Rice", 1800), ("Maize", 2700)]:
        fig3.add_hline(y=base, line_dash="dot", line_color="#94a3b8",
                       annotation_text=f"{crop} maturity (~{base} GDD)",
                       annotation_position="bottom right")
    fig3.update_layout(
        template="plotly_dark", height=260, margin=dict(l=10, r=10, t=20, b=10),
        yaxis_title="Cumulative GDD", xaxis_title="",
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Sowing recommendation
    st.markdown(f"### 🗓️ {t('sowing_rec', lang)}")
    season_color = {"Kharif": "#16a34a", "Rabi": "#2563eb", "Zaid (Summer)": "#d97706", "Transition": "#94a3b8"}
    sc = season_color.get(sowing["season"], "#64748b")

    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:1px solid #bbf7d0;
                        border-radius:10px;padding:16px 20px;margin:10px 0;">
              <div style="font-weight:700;color:{sc};font-size:1rem;margin-bottom:8px;">
                🌿 {sowing['season']} Season — {sowing['note']}
              </div>
              <div style="color:#374151;font-size:0.88rem;">
                <strong>Recommended crops:</strong> {", ".join(sowing['crops'])}
              </div>
              <div style="margin-top:10px;padding-top:10px;border-top:1px solid #d1fae5;
                          color:#64748b;font-size:0.8rem;">
                🌡️ Current 7-day avg temp: <strong>{avg_temp_7d}°C</strong> &nbsp;|&nbsp;
                ❄️ Frost risk: <strong style="color:{'#ef4444' if frost_risk=='High' else '#16a34a'};">{frost_risk}</strong>
              </div>
            </div>""",
        unsafe_allow_html=True,
    )

    # ── Crop heat stress table
    st.markdown("#### Crop Temperature Suitability (Current Week)")
    rows = []
    for crop, base in CROP_BASE_TEMPS.items():
        gdd_week = max(0, avg_temp_7d - base) * 7
        suitability = "✅ Optimal" if gdd_week > 30 else "⚠️ Suboptimal" if gdd_week > 0 else "❌ Too Cold"
        rows.append({"Crop": crop, "GDD Base (°C)": base,
                     "GDD This Week": round(gdd_week, 1), "Suitability": suitability})
    tbl = pd.DataFrame(rows)
    st.dataframe(tbl, use_container_width=True, hide_index=True)
