"""
Disaster Management Module — Eco-Climate Intelligence
Detects heat waves, cold waves, and storm events from historical data.
Generates a risk map overlay using Folium.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from modules.translations import t


def _detect_heat_waves(df: pd.DataFrame, threshold: float = 40.0, min_days: int = 3) -> int:
    """
    Count distinct heat wave events: consecutive days where tmax exceeds threshold.
    We use 40°C for India-relevant definition (IMD standard).
    """
    above = df["tmax"] >= threshold
    event_count = 0
    consecutive = 0
    for flag in above:
        if flag:
            consecutive += 1
        else:
            if consecutive >= min_days:
                event_count += 1
            consecutive = 0
    if consecutive >= min_days:
        event_count += 1
    return event_count


def _detect_cold_waves(df: pd.DataFrame, threshold: float = 10.0, min_days: int = 3) -> int:
    """Cold wave: tmin below threshold for 3+ consecutive days (India plains definition)."""
    below = df["tmin"] <= threshold
    event_count = 0
    consecutive = 0
    for flag in below:
        if flag:
            consecutive += 1
        else:
            if consecutive >= min_days:
                event_count += 1
            consecutive = 0
    if consecutive >= min_days:
        event_count += 1
    return event_count


def _storm_days(df: pd.DataFrame, wind_thresh_kmh: float = 62.0) -> int:
    """Days with peak wind gusts exceeding 62 km/h (gale force)."""
    if "wpgt" in df.columns and df["wpgt"].notna().any():
        return int((df["wpgt"] >= wind_thresh_kmh).sum())
    if "wspd" in df.columns:
        return int((df["wspd"] >= 40).sum())   # 40 km/h sustained if no gust data
    return 0


def _heat_wave_days(df: pd.DataFrame, threshold: float = 40.0) -> int:
    return int((df["tmax"] >= threshold).sum())


def _cold_wave_days(df: pd.DataFrame, threshold: float = 10.0) -> int:
    return int((df["tmin"] <= threshold).sum())


def _overall_risk(hw_events: int, cw_events: int, storm_d: int) -> tuple[str, str]:
    score = hw_events * 3 + cw_events * 2 + storm_d
    if score >= 10:  return "HIGH",     "#ef4444"
    if score >= 5:   return "MODERATE", "#f59e0b"
    return "LOW", "#22c55e"


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


def _build_risk_map(lat: float, lon: float, risk_label: str, risk_color: str,
                    hw_days: int, cw_days: int, storm_days: int) -> folium.Map:
    color_map = {"HIGH": "red", "MODERATE": "orange", "LOW": "green"}
    m = folium.Map(location=[lat, lon], zoom_start=10, tiles="CartoDB positron")

    # City marker
    folium.Marker(
        [lat, lon],
        tooltip=f"<b>Location</b><br>Risk: {risk_label}",
        popup=folium.Popup(
            f"""<div style='font-family:sans-serif;min-width:180px'>
              <b>Extreme Weather Summary</b><br>
              🌡️ Heat wave days: <b>{hw_days}</b><br>
              ❄️ Cold wave days: <b>{cw_days}</b><br>
              🌪️ Storm days: <b>{storm_days}</b><br>
              <span style='color:{risk_color};font-weight:700'>Risk: {risk_label}</span>
            </div>""",
            max_width=220,
        ),
        icon=folium.Icon(color=color_map.get(risk_label, "blue"), icon="warning-sign", prefix="glyphicon"),
    ).add_to(m)

    # Risk radius circles — scaled to risk level
    radius_map = {"HIGH": 25000, "MODERATE": 18000, "LOW": 10000}
    alpha_map  = {"HIGH": 0.25,  "MODERATE": 0.15,  "LOW": 0.08}
    folium.Circle(
        location=[lat, lon],
        radius=radius_map.get(risk_label, 15000),
        color=risk_color, fill=True,
        fill_color=risk_color, fill_opacity=alpha_map.get(risk_label, 0.1),
        tooltip="Primary impact zone",
    ).add_to(m)

    # Outer buffer
    folium.Circle(
        location=[lat, lon], radius=50000,
        color="#94a3b8", fill=True, fill_color="#94a3b8", fill_opacity=0.04,
        tooltip="Monitoring zone (50 km radius)",
    ).add_to(m)

    return m


def render(df: pd.DataFrame, city: str, lat: float, lon: float, lang: str):
    hw_events  = _detect_heat_waves(df)
    cw_events  = _detect_cold_waves(df)
    storm_d    = _storm_days(df)

    hw_days    = _heat_wave_days(df)
    cw_days    = _cold_wave_days(df)

    risk_label, risk_color = _overall_risk(hw_events, cw_events, storm_d)
    avg_max    = round(df["tmax"].mean(), 1)
    avg_min    = round(df["tmin"].mean(), 1)

    # Section header
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#7f1d1d,#ef4444);
                        color:white;padding:18px 22px;border-radius:12px;margin-bottom:18px;">
              <h2 style="margin:0;font-size:1.4rem;">🚨 {t('disaster',lang)}</h2>
              <p style="margin:4px 0 0;opacity:0.85;font-size:0.85rem;">{t('city_label',lang)}: <strong>{city}</strong></p>
            </div>""",
        unsafe_allow_html=True,
    )

    # ── KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric_card(hw_days, t("heat_days", lang), "#ef4444", " days", "tmax ≥ 40°C")
    with c2: _metric_card(cw_days, t("cold_days", lang), "#6366f1", " days", "tmin ≤ 10°C")
    with c3: _metric_card(storm_d, "Storm Days", "#f97316", " days", "gusts ≥ 62 km/h")
    with c4:
        _metric_card(
            risk_label, t("risk_level", lang), risk_color, "",
            f"{hw_events} heat + {cw_events} cold events",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown("**🌡️ Temperature Extremes — Daily Max & Min (3 Years)**")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df.index, y=df["tmax"],
            name="Daily Max", line=dict(color="#ef4444", width=1),
            fill=None, mode="lines",
            hovertemplate="%{x|%b %d %Y}: %{y:.1f}°C<extra>Max</extra>",
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df["tmin"],
            name="Daily Min", line=dict(color="#3b82f6", width=1),
            fill="tonexty", fillcolor="rgba(148,163,184,0.12)", mode="lines",
            hovertemplate="%{x|%b %d %Y}: %{y:.1f}°C<extra>Min</extra>",
        ))
        fig.add_hline(y=40, line_dash="dot", line_color="#ef4444",
                      annotation_text="Heat wave threshold (40°C)")
        fig.add_hline(y=10, line_dash="dot", line_color="#6366f1",
                      annotation_text="Cold wave threshold (10°C)")
        fig.update_layout(
            template="plotly_white", height=300, margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            yaxis_title="°C", xaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("**💨 Wind Speed Distribution**")
        wind_col = "wpgt" if "wpgt" in df.columns and df["wpgt"].notna().any() else "wspd"
        wind_data = df[wind_col].dropna()
        if not wind_data.empty:
            fig2 = go.Figure(go.Histogram(
                x=wind_data, nbinsx=30,
                marker_color="#6366f1", opacity=0.8,
                hovertemplate="Speed: %{x:.0f} km/h<br>Count: %{y}<extra></extra>",
            ))
            fig2.add_vline(x=62, line_dash="dot", line_color="#ef4444",
                           annotation_text="Storm threshold")
            fig2.update_layout(
                template="plotly_white", height=300, margin=dict(l=10, r=10, t=20, b=10),
                xaxis_title="Wind Speed (km/h)", yaxis_title="Days",
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Wind gust data not available for this station.")

    # ── Risk map
    st.markdown(f"### 🗺️ Disaster Risk Zone Map")
    st.caption("Click the marker for the full risk summary. The shaded circle shows the primary impact zone.")
    risk_map = _build_risk_map(lat, lon, risk_label, risk_color, hw_days, cw_days, storm_d)
    st_folium(risk_map, width="100%", height=380, returned_objects=[])

    # ── Alert boxes
    st.markdown(f"### ⚠️ Active Alerts")
    alerts = []
    if hw_days > 30:
        alerts.append(("🌡️ Heat Alert", f"{hw_days} days exceeded 40°C in 3 years. Enforce heat action plans.", "#ef4444", "#fef2f2"))
    if cw_days > 30:
        alerts.append(("❄️ Cold Alert", f"{cw_days} cold days recorded. Vulnerable populations need shelter support.", "#6366f1", "#eef2ff"))
    if storm_d > 10:
        alerts.append(("🌪️ Storm Alert", f"{storm_d} days with extreme wind events. Inspect infrastructure.", "#f97316", "#fff7ed"))
    if not alerts:
        alerts.append(("✅ No Critical Alerts", "Extreme weather frequency is within historically normal ranges.", "#22c55e", "#f0fdf4"))

    for title, msg, color, bg in alerts:
        st.markdown(
            f"""<div style="background:{bg};border-left:4px solid {color};border-radius:8px;
                            padding:12px 16px;margin:6px 0;">
                  <strong style="color:{color};">{title}</strong><br>
                  <span style="color:#374151;font-size:0.87rem;">{msg}</span>
                </div>""",
            unsafe_allow_html=True,
        )
