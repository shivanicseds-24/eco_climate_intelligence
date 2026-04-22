"""
Energy Module — Eco-Climate Intelligence
Computes Heating Degree Days (HDD), Cooling Degree Days (CDD),
grid stress risk, and solar/wind energy potential.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from modules.translations import t

BASE_TEMP = 18.0   # ASHRAE standard balance-point temperature (°C)


def _compute_hdd(df: pd.DataFrame, base: float = BASE_TEMP) -> float:
    """HDD = sum of max(0, base - tavg) across all days."""
    return float(np.maximum(0, base - df["tavg"]).sum())


def _compute_cdd(df: pd.DataFrame, base: float = BASE_TEMP) -> float:
    """CDD = sum of max(0, tavg - base) across all days."""
    return float(np.maximum(0, df["tavg"] - base).sum())


def _peak_demand_days(df: pd.DataFrame, heat_thresh: float = 35.0, cold_thresh: float = 8.0) -> int:
    """Days where temperature extremes drive peak HVAC energy demand."""
    return int(((df["tmax"] >= heat_thresh) | (df["tmin"] <= cold_thresh)).sum())


def _grid_stress_score(cdd: float, hdd: float, peak_days: int) -> tuple[str, str, float]:
    """Normalised 0–100 grid stress score."""
    normalised = min(100, (cdd / 1500 + hdd / 2000) * 40 + peak_days / 300 * 20)
    if normalised >= 65: return "HIGH",     "#ef4444", normalised
    if normalised >= 35: return "MODERATE", "#f59e0b", normalised
    return "LOW", "#22c55e", normalised


def _solar_potential(df: pd.DataFrame) -> str:
    """Rough solar potential from mean temperature and precipitation proxy."""
    avg_temp = df["tavg"].mean()
    avg_rain = df["prcp"].mean()
    if avg_temp > 22 and avg_rain < 3:  return "High ☀️"
    if avg_temp > 15:                   return "Moderate 🌤️"
    return "Low 🌧️"


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
    hdd       = _compute_hdd(df)
    cdd       = _compute_cdd(df)
    peak_days = _peak_demand_days(df)
    grid_label, grid_color, grid_score = _grid_stress_score(cdd, hdd, peak_days)
    solar_pot = _solar_potential(df)

    # Section header
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#1e1b4b,#7c3aed);
                        color:white;padding:18px 22px;border-radius:12px;margin-bottom:18px;">
              <h2 style="margin:0;font-size:1.4rem;">⚡ {t('energy',lang)}</h2>
              <p style="margin:4px 0 0;opacity:0.85;font-size:0.85rem;">{t('city_label',lang)}: <strong>{city}</strong></p>
            </div>""",
        unsafe_allow_html=True,
    )

    # ── KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric_card(f"{int(hdd):,}", t("hdd", lang), "#3b82f6", " HDD", f"base {BASE_TEMP}°C")
    with c2: _metric_card(f"{int(cdd):,}", t("cdd", lang), "#ef4444", " CDD", f"base {BASE_TEMP}°C")
    with c3: _metric_card(f"{peak_days}", t("peak_demand", lang), "#f59e0b", " days", "tmax≥35 or tmin≤8")
    with c4: _metric_card(grid_label, t("grid_stress", lang), grid_color, "", f"Score: {grid_score:.0f}/100")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("**📊 Monthly HDD vs CDD (3-Year)**")
        monthly = df.groupby(["year", "month"])["tavg"].mean().reset_index()
        monthly["HDD"] = np.maximum(0, BASE_TEMP - monthly["tavg"])
        monthly["CDD"] = np.maximum(0, monthly["tavg"] - BASE_TEMP)
        monthly["date_label"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly["date_label"], y=monthly["HDD"],
            name="HDD (Heating)", marker_color="#3b82f6",
            hovertemplate="%{x}: %{y:.0f} HDD<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            x=monthly["date_label"], y=monthly["CDD"],
            name="CDD (Cooling)", marker_color="#ef4444",
            hovertemplate="%{x}: %{y:.0f} CDD<extra></extra>",
        ))
        fig.update_layout(
            template="plotly_white", barmode="stack",
            height=280, margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
            yaxis_title="Degree Days", xaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("**📈 Energy Demand Pattern (Daily Avg Temp)**")
        daily_sample = df["tavg"].resample("W").mean().reset_index()
        daily_sample.columns = ["date", "tavg"]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=daily_sample["date"], y=daily_sample["tavg"],
            fill="tozeroy",
            fillcolor=[
                "rgba(59,130,246,0.15)" if v < BASE_TEMP else "rgba(239,68,68,0.12)"
                for v in daily_sample["tavg"]
            ][0],
            line=dict(color="#7c3aed", width=2),
            name="Weekly Avg Temp",
            hovertemplate="%{x|%b %d %Y}: %{y:.1f}°C<extra></extra>",
        ))
        fig2.add_hline(y=BASE_TEMP, line_dash="dash", line_color="#64748b",
                       annotation_text=f"Balance point ({BASE_TEMP}°C)")
        fig2.update_layout(
            template="plotly_white", height=280, margin=dict(l=10, r=10, t=20, b=10),
            yaxis_title="°C", xaxis_title="",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Grid stress gauge
    st.markdown("### ⚡ Grid Stress Indicator")
    fig3 = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=grid_score,
        number={"suffix": "/100", "font": {"size": 36}},
        delta={"reference": 50, "increasing": {"color": "#ef4444"}, "decreasing": {"color": "#22c55e"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748b"},
            "bar": {"color": grid_color},
            "steps": [
                {"range": [0,  35], "color": "#dcfce7"},
                {"range": [35, 65], "color": "#fef9c3"},
                {"range": [65,100], "color": "#fee2e2"},
            ],
            "threshold": {
                "line": {"color": "#1e293b", "width": 3},
                "thickness": 0.75, "value": grid_score,
            },
        },
        title={"text": f"Grid Stress Score — {grid_label}", "font": {"size": 16}},
    ))
    fig3.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=10))
    st.plotly_chart(fig3, use_container_width=True)

    # ── Renewable energy potential panel
    st.markdown("### ☀️ Renewable Energy Potential")
    renew_col1, renew_col2 = st.columns(2)

    with renew_col1:
        st.markdown(
            f"""<div style="background:linear-gradient(135deg,#fef9c3,#fef08a);border:1px solid #fde68a;
                            border-radius:10px;padding:16px 18px;">
                  <div style="font-size:1.1rem;font-weight:700;color:#92400e;margin-bottom:8px;">☀️ Solar PV Potential</div>
                  <div style="font-size:1.6rem;font-weight:700;color:#78350f;">{solar_pot}</div>
                  <div style="font-size:0.82rem;color:#92400e;margin-top:8px;">
                    Based on mean temperature ({df["tavg"].mean():.1f}°C) and precipitation pattern.
                    {'Strong candidate for rooftop solar deployment.' if 'High' in solar_pot else
                     'Viable with moderate panel efficiency requirements.' if 'Moderate' in solar_pot else
                     'Supplementary storage essential for viability.'}
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )

    with renew_col2:
        wind_col = "wspd" if "wspd" in df.columns else None
        avg_wind = round(df[wind_col].mean(), 1) if wind_col else 0.0
        wind_class = "High 🌬️" if avg_wind > 20 else "Moderate 💨" if avg_wind > 10 else "Low 🌫️"
        st.markdown(
            f"""<div style="background:linear-gradient(135deg,#dbeafe,#bfdbfe);border:1px solid #93c5fd;
                            border-radius:10px;padding:16px 18px;">
                  <div style="font-size:1.1rem;font-weight:700;color:#1e3a8a;margin-bottom:8px;">🌬️ Wind Energy Potential</div>
                  <div style="font-size:1.6rem;font-weight:700;color:#1e40af;">{wind_class}</div>
                  <div style="font-size:0.82rem;color:#1e3a8a;margin-top:8px;">
                    3-year mean wind speed: <strong>{avg_wind} km/h</strong>.<br>
                    {'Suitable for utility-scale wind farms.' if 'High' in wind_class else
                     'Small turbines and hybrid systems are cost-effective.' if 'Moderate' in wind_class else
                     'Wind energy is not economically viable at this location.'}
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )

    # ── Seasonal recommendations
    st.markdown(
        """<div style="background:#f5f3ff;border-left:4px solid #7c3aed;border-radius:8px;
                        padding:14px 18px;margin-top:14px;">
              <strong>⚡ Energy Planning Recommendations</strong>
              <ul style="color:#374151;font-size:0.87rem;margin:10px 0 0;padding-left:18px;">
                <li>Procure additional peaking capacity before the top 3 CDD months.</li>
                <li>Implement demand-response programs during extreme heat and cold days.</li>
                <li>Invest in battery storage to buffer renewable intermittency.</li>
                <li>Retrofit government buildings with insulation to reduce HDD-linked gas demand.</li>
              </ul>
            </div>""",
        unsafe_allow_html=True,
    )
