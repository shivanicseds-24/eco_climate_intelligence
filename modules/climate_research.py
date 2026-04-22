"""
Climate Research Module — Eco-Climate Intelligence
Performs trend analysis via linear regression, detects temperature anomalies,
and presents long-range warming signals from 3-year historical data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
from modules.translations import t


def _linear_trend(series: pd.Series) -> tuple[float, float, float]:
    """
    Fit a linear regression to the series (indexed 0, 1, 2, …).
    Returns (slope_per_unit, r_squared, p_value).
    """
    x = np.arange(len(series))
    y = series.values
    mask = ~np.isnan(y)
    if mask.sum() < 10:
        return 0.0, 0.0, 1.0
    slope, intercept, r, p, se = stats.linregress(x[mask], y[mask])
    return float(slope), float(r ** 2), float(p)


def _anomaly_series(df: pd.DataFrame) -> pd.Series:
    """
    Monthly temp anomaly relative to the 3-year monthly mean.
    Positive = warmer than the reference period for that calendar month.
    """
    monthly_avg = df.groupby(["year", "month"])["tavg"].mean().reset_index()
    ref = monthly_avg.groupby("month")["tavg"].mean()
    monthly_avg["anomaly"] = monthly_avg.apply(
        lambda row: row["tavg"] - ref.loc[row["month"]], axis=1
    )
    monthly_avg.index = pd.to_datetime(
        monthly_avg["year"].astype(str) + "-" + monthly_avg["month"].astype(str).str.zfill(2) + "-01"
    )
    return monthly_avg["anomaly"]


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
    # ── Annual averages
    annual = df.groupby("year").agg(
        tavg=("tavg", "mean"),
        tmax=("tmax", "mean"),
        tmin=("tmin", "mean"),
        prcp=("prcp", "sum"),
    ).reset_index()

    # Linear trend on annual avg temp
    slope_per_yr, r2, pval = _linear_trend(annual["tavg"])
    slope_per_decade = round(slope_per_yr * 10, 3)

    # Anomaly series
    anomaly = _anomaly_series(df)
    latest_anomaly = round(float(anomaly.iloc[-1]), 2) if not anomaly.empty else 0.0
    warm_months    = int((anomaly > 0.5).sum())
    extreme_warm   = int((anomaly > 1.0).sum())

    # Section header
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#0f172a,#1e40af);
                        color:white;padding:18px 22px;border-radius:12px;margin-bottom:18px;">
              <h2 style="margin:0;font-size:1.4rem;">🔬 {t('climate',lang)}</h2>
              <p style="margin:4px 0 0;opacity:0.85;font-size:0.85rem;">{t('city_label',lang)}: <strong>{city}</strong></p>
            </div>""",
        unsafe_allow_html=True,
    )

    # ── KPIs
    trend_color = "#ef4444" if slope_per_decade > 0.1 else "#f59e0b" if slope_per_decade > 0 else "#22c55e"
    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric_card(f"{slope_per_decade:+.3f}", t("warming_rate", lang), trend_color, "°C/decade", "linear regression")
    with c2: _metric_card(f"{latest_anomaly:+.2f}", t("anomaly", lang), "#f97316", "°C", "vs 3-yr monthly avg")
    with c3: _metric_card(f"{warm_months}", "Warm Months", "#ef4444", "", "anomaly > +0.5°C")
    with c4: _metric_card(f"{round(r2, 3)}", "Trend R²", "#3b82f6", "", f"p = {pval:.3f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts: Annual temperature trend
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown(f"**📈 {t('annual_temp', lang)} with Linear Trend**")
        # Trend line
        x_fit = np.arange(len(annual))
        slope_raw, intercept_raw, *_ = stats.linregress(x_fit, annual["tavg"].values)
        trend_vals = slope_raw * x_fit + intercept_raw

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=annual["year"], y=annual["tmax"],
            name="Annual Max", line=dict(color="#ef4444", width=1.5, dash="dot"),
        ))
        fig.add_trace(go.Scatter(
            x=annual["year"], y=annual["tavg"],
            name="Annual Avg", fill=None, mode="lines+markers",
            line=dict(color="#f97316", width=2.5),
            marker=dict(size=7, color="#f97316"),
        ))
        fig.add_trace(go.Scatter(
            x=annual["year"], y=trend_vals,
            name=f"Trend ({slope_per_decade:+.3f}°C/decade)",
            line=dict(color="#7c3aed", width=2, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x=annual["year"], y=annual["tmin"],
            name="Annual Min", line=dict(color="#3b82f6", width=1.5, dash="dot"),
        ))
        fig.update_layout(
            template="plotly_white", height=300, margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"),
            yaxis_title="°C", xaxis_title="Year",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("**🌡️ Monthly Temperature Anomaly**")
        anomaly_df = anomaly.reset_index()
        anomaly_df.columns = ["date", "anomaly"]

        fig2 = go.Figure(go.Bar(
            x=anomaly_df["date"],
            y=anomaly_df["anomaly"],
            marker_color=[
                "#ef4444" if v > 0.5 else "#f97316" if v > 0 else "#3b82f6" if v > -0.5 else "#1e40af"
                for v in anomaly_df["anomaly"]
            ],
            hovertemplate="%{x|%b %Y}: %{y:+.2f}°C<extra></extra>",
        ))
        fig2.add_hline(y=0, line_color="#64748b", line_width=1)
        fig2.add_hline(y=1, line_dash="dot", line_color="#ef4444",
                       annotation_text="Extreme warm (+1°C)")
        fig2.add_hline(y=-1, line_dash="dot", line_color="#3b82f6",
                       annotation_text="Extreme cold (−1°C)")
        fig2.update_layout(
            template="plotly_white", height=300, margin=dict(l=10, r=10, t=20, b=10),
            yaxis_title="°C anomaly", xaxis_title="",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Annual precipitation trend
    st.markdown("**🌧️ Annual Precipitation Trend**")
    prcp_slope, _, _ = _linear_trend(annual["prcp"])
    prcp_per_yr = round(prcp_slope, 1)
    prcp_color  = "#0369a1" if prcp_per_yr >= 0 else "#f59e0b"

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=annual["year"], y=annual["prcp"],
        marker_color="#0ea5e9", name="Annual Rainfall",
        hovertemplate="%{x}: %{y:.0f} mm<extra></extra>",
    ))
    prcp_x = np.arange(len(annual))
    prcp_slope_raw, prcp_int, *_ = stats.linregress(prcp_x, annual["prcp"].values)
    prcp_trend = prcp_slope_raw * prcp_x + prcp_int
    fig3.add_trace(go.Scatter(
        x=annual["year"], y=prcp_trend,
        name=f"Trend ({prcp_per_yr:+.1f} mm/yr)",
        line=dict(color="#7c3aed", width=2, dash="dash"),
    ))
    fig3.update_layout(
        template="plotly_white", height=240, margin=dict(l=10, r=10, t=20, b=10),
        yaxis_title="mm", xaxis_title="Year",
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Scientific interpretation
    st.markdown("### 🧪 Scientific Interpretation")
    interp_text = (
        f"Over the available {df['year'].nunique()}-year record, **{city}** shows a warming trend of "
        f"**{slope_per_decade:+.3f}°C per decade** (R² = {r2:.3f}, p = {pval:.3f}). "
    )
    if pval < 0.05:
        interp_text += "This trend is **statistically significant** at the 95% confidence level. "
    else:
        interp_text += "The trend is not yet statistically significant due to the short record length — a longer series would be needed for conclusive attribution. "

    if slope_per_decade > 0:
        interp_text += (
            f"The most recent month showed an anomaly of **{latest_anomaly:+.2f}°C** relative to the "
            f"3-year monthly baseline, and **{warm_months}** months recorded anomalies above +0.5°C. "
            f"These patterns are consistent with regional warming signals observed across South Asia."
        )
    else:
        interp_text += "The slight cooling trend may reflect local land-cover change, aerosol effects, or natural variability — further analysis is recommended."

    st.markdown(
        f"""<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;
                        padding:16px 20px;color:#0c4a6e;font-size:0.9rem;line-height:1.7;">
              {interp_text}
            </div>""",
        unsafe_allow_html=True,
    )

    # ── Data quality badge
    total_days    = len(df)
    expected_days = df["year"].nunique() * 365
    coverage_pct  = round(min(total_days / expected_days * 100, 100), 1)
    st.markdown(
        f"""<div style="background:#f8fafc;border-radius:8px;padding:10px 14px;margin-top:10px;
                        font-size:0.8rem;color:#64748b;display:flex;gap:16px;">
              📅 <strong>Data Coverage:</strong> {total_days:,} daily records ({coverage_pct}% of expected) &nbsp;|&nbsp;
              📡 <strong>Source:</strong> Meteostat API &nbsp;|&nbsp;
              📍 <strong>Location:</strong> {lat}°N, {lon}°E
            </div>""",
        unsafe_allow_html=True,
    )
