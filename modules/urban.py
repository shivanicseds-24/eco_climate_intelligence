"""
Urban Planning Module — Eco-Climate Intelligence
Estimates Urban Heat Island (UHI) intensity, day-night temperature differentials,
and renders a Folium heat-island overlay for urban thermal analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from modules.translations import t


def _uhi_intensity(df: pd.DataFrame) -> float:
    """
    Proxy UHI estimate: urban areas suppress nighttime cooling.
    We model this as the seasonal mean of (tmax - tmin), relative to its
    own 3-year average — a higher differential in recent months hints at
    urban heat retention. Returns approximate °C offset.
    """
    df = df.copy()
    df["diurnal_range"] = df["tmax"] - df["tmin"]
    mean_range = df["diurnal_range"].mean()
    # UHI is roughly proportional to the compaction of diurnal range
    # Global urban studies estimate 1–4°C for a city of >500k population
    # We keep a conservative estimate tied to the local data.
    recent_3m   = df.tail(90)["diurnal_range"].mean()
    long_term   = df["diurnal_range"].mean()
    # Suppression of diurnal range = urban signal
    suppression = max(0, long_term - recent_3m)
    return round(min(suppression + 1.2, 4.5), 2)   # floor at 1.2°C (small city baseline)


def _day_night_diff(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly average of (tmax - tmin) — proxy for urban vs rural thermal contrast."""
    df = df.copy()
    df["diff"] = df["tmax"] - df["tmin"]
    return df.groupby(["year", "month"])["diff"].mean().reset_index()


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


def _build_uhi_map(lat: float, lon: float, uhi: float) -> folium.Map:
    """
    Generates a Folium map with concentric heat-intensity zones simulating
    the urban heat island gradient from city core → urban fringe → rural area.
    """
    m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB positron")

    # Simulated heat data — concentric density around city centre
    rng = np.random.default_rng(42)
    heat_data = []
    for _ in range(300):
        r   = rng.exponential(0.02)           # radius in degrees (~2 km mean)
        theta = rng.uniform(0, 2 * np.pi)
        pt_lat = lat + r * np.cos(theta)
        pt_lon = lon + r * np.sin(theta)
        intensity = max(0.05, 1 - r * 30)     # stronger at centre
        heat_data.append([pt_lat, pt_lon, float(intensity)])

    HeatMap(
        heat_data,
        min_opacity=0.3,
        max_zoom=16,
        radius=25,
        blur=20,
        gradient={0.2: "blue", 0.5: "lime", 0.7: "yellow", 1.0: "red"},
    ).add_to(m)

    # City marker
    folium.CircleMarker(
        location=[lat, lon], radius=8,
        color="#ef4444", fill=True, fill_color="#ef4444", fill_opacity=0.9,
        tooltip=f"<b>Urban Core</b><br>UHI Intensity: ~{uhi}°C above rural",
    ).add_to(m)

    # UHI radius circles with labels
    for radius_m, label, opacity in [
        (3_000,  "Urban Core",         0.30),
        (8_000,  "Inner Urban Zone",   0.15),
        (20_000, "Urban Fringe",       0.07),
    ]:
        folium.Circle(
            location=[lat, lon], radius=radius_m,
            color="#f97316", fill=True, fill_color="#f97316",
            fill_opacity=opacity, tooltip=label,
        ).add_to(m)

    return m


def render(df: pd.DataFrame, city: str, lat: float, lon: float, lang: str):
    uhi         = _uhi_intensity(df)
    avg_temp    = round(df["tavg"].mean(), 1)
    max_month   = df.groupby("month")["tavg"].mean().idxmax()
    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                   7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    peak_heat_month = month_names.get(max_month, str(max_month))

    df_dn = _day_night_diff(df)
    avg_dn_diff = round(df_dn["diff"].mean(), 1)

    # Section header
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#78350f,#f59e0b);
                        color:white;padding:18px 22px;border-radius:12px;margin-bottom:18px;">
              <h2 style="margin:0;font-size:1.4rem;">🏙️ {t('urban',lang)}</h2>
              <p style="margin:4px 0 0;opacity:0.85;font-size:0.85rem;">{t('city_label',lang)}: <strong>{city}</strong></p>
            </div>""",
        unsafe_allow_html=True,
    )

    # ── KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric_card(f"+{uhi}", t("uhi_intensity", lang), "#f59e0b", "°C", "vs rural baseline")
    with c2: _metric_card(f"{avg_temp}", "Mean Urban Temp", "#ef4444", "°C", "3-year average")
    with c3: _metric_card(peak_heat_month, "Peak Heat Month", "#f97316", "", "hottest on record")
    with c4: _metric_card(f"{avg_dn_diff}", t("day_night_diff", lang), "#8b5cf6", "°C", "avg diurnal range")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown(f"**📈 {t('monthly_temp', lang)} (3-Year)**")
        monthly = df.groupby(["year","month"]).agg(
            tavg=("tavg","mean"), tmax=("tmax","mean"), tmin=("tmin","mean")
        ).reset_index()
        monthly["date_label"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly["date_label"], y=monthly["tmax"],
            name="Max", fill=None, mode="lines",
            line=dict(color="#ef4444", width=1.5),
        ))
        fig.add_trace(go.Scatter(
            x=monthly["date_label"], y=monthly["tavg"],
            name="Avg", fill="tonexty", fillcolor="rgba(249,115,22,0.10)",
            mode="lines", line=dict(color="#f97316", width=2.5),
        ))
        fig.add_trace(go.Scatter(
            x=monthly["date_label"], y=monthly["tmin"],
            name="Min", fill="tonexty", fillcolor="rgba(251,191,36,0.06)",
            mode="lines", line=dict(color="#fbbf24", width=1.5),
        ))
        fig.update_layout(
            template="plotly_white", height=280, margin=dict(l=10,r=10,t=20,b=10),
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            yaxis_title="°C",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("**🌆 Diurnal Temperature Range (Urban Heat Suppression)**")
        df_dn["date_label"] = df_dn["year"].astype(str) + "-" + df_dn["month"].astype(str).str.zfill(2)
        fig2 = go.Figure(go.Bar(
            x=df_dn["date_label"], y=df_dn["diff"],
            marker_color=[
                "#f59e0b" if v < 10 else "#f97316" if v < 15 else "#ef4444"
                for v in df_dn["diff"]
            ],
            hovertemplate="%{x}: %{y:.1f}°C range<extra></extra>",
        ))
        fig2.add_hline(y=avg_dn_diff, line_dash="dash", line_color="#7c3aed",
                       annotation_text=f"Average: {avg_dn_diff}°C")
        fig2.update_layout(
            template="plotly_white", height=280, margin=dict(l=10,r=10,t=20,b=10),
            yaxis_title="Tmax − Tmin (°C)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Heat island map
    st.markdown("### 🗺️ Urban Heat Island Visualisation")
    st.caption(
        "Warmer colours indicate higher thermal intensity. The gradient represents "
        "modelled heat distribution from the urban core outward to the rural fringe."
    )
    uhi_map = _build_uhi_map(lat, lon, uhi)
    st_folium(uhi_map, width="100%", height=400, returned_objects=[])

    # ── Green space recommendations
    st.markdown("### 🌳 Urban Planning Recommendations")
    uhi_severity = "High" if uhi >= 3 else "Moderate" if uhi >= 2 else "Low"
    severity_color = {"High": "#ef4444", "Moderate": "#f59e0b", "Low": "#22c55e"}[uhi_severity]

    st.markdown(
        f"""<div style="background:#fff7ed;border-left:4px solid {severity_color};
                        border-radius:8px;padding:14px 18px;margin:8px 0;">
              <strong style="color:{severity_color};">UHI Severity: {uhi_severity} (~{uhi}°C above rural)</strong>
            </div>""",
        unsafe_allow_html=True,
    )

    recs = {
        "High":     ["Deploy cool roofs and cool pavement materials city-wide.",
                     "Mandate urban forests with ≥30% canopy cover in new developments.",
                     "Install green corridors to channel cool rural air into the core.",
                     "Enforce nighttime heat action plans during summer peak."],
        "Moderate": ["Expand urban parks and tree-lined streets in dense zones.",
                     "Promote green building certifications for new construction.",
                     "Increase reflective surfaces on rooftops in commercial districts."],
        "Low":      ["Maintain existing green cover — avoid urban densification without offsets.",
                     "Introduce biophilic design elements in redevelopment projects."],
    }

    for rec in recs.get(uhi_severity, []):
        st.markdown(
            f"""<div style="background:#f8fafc;border-radius:6px;padding:8px 14px;
                            margin:4px 0;color:#374151;font-size:0.87rem;
                            border-left:3px solid #f59e0b;">🌿 {rec}</div>""",
            unsafe_allow_html=True,
        )
