"""
Water Resources Module — Eco-Climate Intelligence
Computes the Standardised Precipitation Index (SPI), flood risk score,
and drought classification from 3-year historical precipitation data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
from modules.translations import t


def _compute_spi(monthly_prcp: pd.Series, scale: int = 3) -> pd.Series:
    """
    A simplified SPI: standardise precipitation at the given time scale
    by fitting a normal distribution to the rolling sum.
    SPI > 2 = extremely wet; SPI < -2 = extreme drought.
    """
    rolling = monthly_prcp.rolling(scale).sum()
    mean = rolling.mean()
    std  = rolling.std()
    spi  = (rolling - mean) / (std + 1e-9)
    return spi.clip(-3, 3)


def _drought_class(spi: float) -> tuple[str, str]:
    """Return (label, colour) for a given SPI value."""
    if spi >= 2:     return "Extremely Wet", "#1e40af"
    if spi >= 1:     return "Moderately Wet", "#3b82f6"
    if spi >= -0.5:  return "Near Normal",    "#22c55e"
    if spi >= -1:    return "Mild Drought",   "#f59e0b"
    if spi >= -1.5:  return "Moderate Drought","#f97316"
    if spi >= -2:    return "Severe Drought",  "#ef4444"
    return "Extreme Drought", "#7f1d1d"


def _metric_card(value, label, color="#028090", unit="", sub=""):
    st.markdown(
        f"""<div style="background:white;border-radius:12px;padding:18px 14px;text-align:center;
                        box-shadow:0 2px 10px rgba(0,0,0,0.07);border-top:4px solid {color};">
              <div style="font-size:1.9rem;font-weight:700;color:#1e293b;">{value}<span style="font-size:1rem;color:#64748b;">{unit}</span></div>
              <div style="font-size:0.75rem;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:0.5px;">{label}</div>
              {"<div style='font-size:0.7rem;color:#94a3b8;margin-top:2px;'>"+sub+"</div>" if sub else ""}
            </div>""",
        unsafe_allow_html=True,
    )


def render(df: pd.DataFrame, city: str, lat: float, lon: float, lang: str):
    # ── Monthly aggregation
    monthly = df.groupby(["year", "month"])["prcp"].sum().reset_index()
    monthly["date_label"] = (
        monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)
    )
    monthly["spi"] = _compute_spi(monthly["prcp"], scale=3)

    overall_spi     = round(float(monthly["spi"].dropna().iloc[-1]), 2)
    spi_label, spi_color = _drought_class(overall_spi)

    avg_monthly_rain = round(monthly["prcp"].mean(), 1)
    total_rain_3yr   = round(df["prcp"].sum(), 0)

    # Flood risk: months with > 200 mm
    flood_months = int((monthly["prcp"] > 200).sum())
    flood_risk_level = "High" if flood_months > 6 else "Moderate" if flood_months > 2 else "Low"
    flood_color      = {"High": "#ef4444", "Moderate": "#f59e0b", "Low": "#22c55e"}[flood_risk_level]

    # Section header
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#0369a1,#0ea5e9);
                        color:white;padding:18px 22px;border-radius:12px;margin-bottom:18px;">
              <h2 style="margin:0;font-size:1.4rem;">💧 {t('water',lang)}</h2>
              <p style="margin:4px 0 0;opacity:0.85;font-size:0.85rem;">{t('city_label',lang)}: <strong>{city}</strong></p>
            </div>""",
        unsafe_allow_html=True,
    )

    # ── KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric_card(f"{avg_monthly_rain}", t("avg_rainfall", lang), "#0ea5e9", " mm", "3-yr monthly avg")
    with c2: _metric_card(f"{overall_spi:+.2f}", t("spi", lang), spi_color, "", spi_label)
    with c3: _metric_card(f"{flood_months}", t("flood_risk", lang), flood_color, " months", "> 200 mm/mo")
    with c4: _metric_card(f"{int(total_rain_3yr)}", t("total_rain", lang), "#0369a1", " mm", "3-year total")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("**🌧️ Monthly Precipitation — Historical vs Average**")
        overall_mean = monthly["prcp"].mean()
        bar_colors = [
            "#1e40af" if v > 200 else "#0ea5e9" if v > overall_mean else "#7dd3fc"
            for v in monthly["prcp"]
        ]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly["date_label"], y=monthly["prcp"],
            marker_color=bar_colors, name="Monthly Rain",
            hovertemplate="%{x}: %{y:.0f} mm<extra></extra>",
        ))
        fig.add_hline(y=overall_mean, line_dash="dash", line_color="#f59e0b",
                      annotation_text=f"3yr avg: {overall_mean:.0f} mm")
        fig.add_hline(y=200, line_dash="dot", line_color="#ef4444",
                      annotation_text="Flood threshold (200 mm)")
        fig.update_layout(
            template="plotly_white", height=280, margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title="mm", xaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("**📊 Standardised Precipitation Index (SPI-3)**")
        spi_valid = monthly.dropna(subset=["spi"])
        bar_spi_colors = [
            "#1e40af" if v >= 1 else "#22c55e" if v >= -0.5 else
            "#f59e0b" if v >= -1 else "#ef4444"
            for v in spi_valid["spi"]
        ]
        fig2 = go.Figure(go.Bar(
            x=spi_valid["date_label"], y=spi_valid["spi"],
            marker_color=bar_spi_colors,
            hovertemplate="%{x}: SPI = %{y:.2f}<extra></extra>",
        ))
        fig2.add_hline(y=-1, line_dash="dot", line_color="#ef4444",
                       annotation_text="Drought threshold")
        fig2.add_hline(y=1, line_dash="dot", line_color="#3b82f6",
                       annotation_text="Wet threshold")
        fig2.update_layout(
            template="plotly_white", height=280, margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title="SPI", xaxis_title="",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Risk assessment panel
    st.markdown(f"### 🔍 {t('risk_assessment', lang)}")

    risk_col1, risk_col2 = st.columns(2)

    with risk_col1:
        drought_label, drought_color = _drought_class(overall_spi)
        st.markdown(
            f"""<div style="background:#fefce8;border-left:4px solid {drought_color};
                            border-radius:8px;padding:14px 16px;margin:6px 0;">
                  <strong style="color:{drought_color};">🌵 {t('drought_risk',lang)}: {drought_label}</strong><br>
                  <span style="color:#64748b;font-size:0.85rem;margin-top:4px;display:block;">
                    SPI-3 index: <strong>{overall_spi:+.2f}</strong> (based on last 3 months rolling average).<br>
                    {"⚠️ Initiate water conservation measures." if overall_spi < -1 else "✅ Precipitation levels are within acceptable range."}
                  </span>
                </div>""",
            unsafe_allow_html=True,
        )

    with risk_col2:
        st.markdown(
            f"""<div style="background:#eff6ff;border-left:4px solid {flood_color};
                            border-radius:8px;padding:14px 16px;margin:6px 0;">
                  <strong style="color:{flood_color};">🌊 {t('flood_risk',lang)}: {flood_risk_level}</strong><br>
                  <span style="color:#64748b;font-size:0.85rem;margin-top:4px;display:block;">
                    {flood_months} month(s) exceeded 200 mm over the past 3 years.<br>
                    {"⚠️ Strengthen drainage and early warning systems." if flood_risk_level == "High" else
                     "⚡ Monitor during monsoon months closely." if flood_risk_level == "Moderate" else
                     "✅ Flood events are infrequent for this location."}
                  </span>
                </div>""",
            unsafe_allow_html=True,
        )

    # ── Seasonal rainfall breakdown
    st.markdown("#### Seasonal Rainfall Distribution (3-Year Average)")
    season_map = {12: "Winter", 1: "Winter", 2: "Winter",
                  3: "Pre-Monsoon", 4: "Pre-Monsoon", 5: "Pre-Monsoon",
                  6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
                  10: "Post-Monsoon", 11: "Post-Monsoon"}
    df_season = df.copy()
    df_season["season"] = df_season["month"].map(season_map)
    seasonal = df_season.groupby("season")["prcp"].sum().reset_index()
    seasonal["share_pct"] = seasonal["prcp"] / seasonal["prcp"].sum() * 100

    fig3 = go.Figure(go.Pie(
        labels=seasonal["season"], values=seasonal["prcp"].round(0),
        hole=0.45,
        marker_colors=["#0ea5e9", "#22c55e", "#f59e0b", "#6366f1"],
        textinfo="label+percent",
        hovertemplate="%{label}: %{value:.0f} mm (%{percent})<extra></extra>",
    ))
    fig3.update_layout(
        height=260, margin=dict(l=10, r=10, t=20, b=10),
        showlegend=True, legend=dict(orientation="h"),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Recommendations
    st.markdown(
        """<div style="background:linear-gradient(135deg,#f0fdf4,#dbeafe);border:1px solid #bfdbfe;
                        border-radius:10px;padding:16px 20px;margin-top:10px;">
              <strong>💡 Water Management Recommendations</strong>
              <ul style="color:#374151;font-size:0.87rem;margin:10px 0 0 0;padding-left:18px;">
                <li>Install rainwater harvesting systems during high-precipitation months.</li>
                <li>Use deficit irrigation scheduling during mild drought (SPI −0.5 to −1).</li>
                <li>Maintain flood-buffering green cover in catchment areas.</li>
                <li>Monitor groundwater recharge rates monthly.</li>
              </ul>
            </div>""",
        unsafe_allow_html=True,
    )
