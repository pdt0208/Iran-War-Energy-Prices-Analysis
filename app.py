import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Iran War – Energy Market Dashboard",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252840);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border-left: 4px solid #e63946;
        margin-bottom: 0.5rem;
    }
    .metric-card h4 { color: #a0aec0; font-size: 0.78rem; margin: 0 0 4px; letter-spacing: 0.08em; text-transform: uppercase; }
    .metric-card h2 { color: #f1f5f9; font-size: 1.6rem; margin: 0; }
    .metric-card small { color: #e63946; font-size: 0.8rem; }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #cbd5e0;
        padding: 0.5rem 0;
        border-bottom: 1px solid #2d3748;
        margin-bottom: 1rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    div[data-testid="stMetric"] { background: #1a1d2e; border-radius: 10px; padding: 1rem; border: 1px solid #2d3748; }
</style>
""", unsafe_allow_html=True)

WAR_DATE = pd.Timestamp("2026-02-27")
WAR_DATE_STR = "2026-02-27"  # string version for plotly add_vline
PHASE_COLORS = {
    "Pre-War": "#4ade80",
    "Active Conflict": "#f87171",
    "Ceasefire": "#fbbf24",
    "Post-War": "#60a5fa",
}

# ── Data Loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    oil = pd.read_csv("iran_war_oil_prices_daily_2026.csv")
    gas = pd.read_csv("iran_war_gas_prices_by_state.csv")
    key = pd.read_csv("iran_war_key_events_timeline.csv")

    oil["date"] = pd.to_datetime(oil["date"])
    key["date"] = pd.to_datetime(key["date"])

    # Drop unneeded cols if they exist
    for col in ["key_event", "source", "data_as_of"]:
        if col in oil.columns:
            oil.drop(columns=[col], inplace=True)
    if "source" in gas.columns:
        gas.drop(columns=["source"], inplace=True)
    if "description" in key.columns:
        key.drop(columns=["description"], inplace=True)
    if "source" in key.columns:
        key.drop(columns=["source"], inplace=True)

    return oil, gas, key

try:
    df_oil, df_gas, df_key = load_data()
    data_loaded = True
except FileNotFoundError as e:
    data_loaded = False
    missing = str(e)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Flag_of_Iran.svg/240px-Flag_of_Iran.svg.png", width=80)
    st.title("🛢️ Iran War\nEnergy Dashboard")
    st.markdown("---")

    if data_loaded:
        phases = ["All"] + sorted(df_oil["phase"].dropna().unique().tolist()) if "phase" in df_oil.columns else ["All"]
        selected_phase = st.selectbox("Filter by Phase", phases)

        date_range = st.date_input(
            "Date Range",
            value=(df_oil["date"].min().date(), df_oil["date"].max().date()),
            min_value=df_oil["date"].min().date(),
            max_value=df_oil["date"].max().date(),
        )

        oil_metrics = st.multiselect(
            "Oil Price Metrics",
            ["brent_usd_barrel", "wti_usd_barrel", "dubai_usd_barrel"],
            default=["brent_usd_barrel", "wti_usd_barrel", "dubai_usd_barrel"],
            format_func=lambda x: x.replace("_usd_barrel", "").upper(),
        )

        st.markdown("---")
        st.caption("War Start: Feb 27, 2026")
        st.caption("Data: Simulated / Educational")

# ── Main Content ──────────────────────────────────────────────────────────────
st.title("🛢️ Iran War – Energy Market Impact Analysis")
st.caption("Live dashboard tracking oil prices, gas prices, and Strait of Hormuz shipping traffic")
st.markdown("---")

if not data_loaded:
    st.error(f"⚠️ Could not load data files. Make sure the CSV files are in the same folder as this script.\n\n`{missing}`")
    st.info("Expected files:\n- `iran_war_oil_prices_daily_2026.csv`\n- `iran_war_gas_prices_by_state.csv`\n- `iran_war_key_events_timeline.csv`")
    st.stop()

# ── Apply Filters ─────────────────────────────────────────────────────────────
df_filtered = df_oil.copy()
if len(date_range) == 2:
    df_filtered = df_filtered[
        (df_filtered["date"] >= pd.Timestamp(date_range[0])) &
        (df_filtered["date"] <= pd.Timestamp(date_range[1]))
    ]
if selected_phase != "All" and "phase" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["phase"] == selected_phase]

before_war = df_oil[df_oil["date"] <= WAR_DATE]
after_war  = df_oil[df_oil["date"] > WAR_DATE]

# ── KPI Cards ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Key Metrics</div>', unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

brent_max = df_oil["brent_usd_barrel"].max() if "brent_usd_barrel" in df_oil.columns else 0
wti_max   = df_oil["wti_usd_barrel"].max()   if "wti_usd_barrel"   in df_oil.columns else 0
ships_before = before_war["strait_hormuz_daily_ships"].sum() if "strait_hormuz_daily_ships" in df_oil.columns else 0
ships_after  = after_war["strait_hormuz_daily_ships"].sum()  if "strait_hormuz_daily_ships" in df_oil.columns else 0
ships_pct    = ((ships_after - ships_before) / ships_before * 100) if ships_before else 0
gas_max      = df_gas["gas_price_mar19_2026"].max() if "gas_price_mar19_2026" in df_gas.columns else 0
avg_pct_inc  = df_gas["pct_increase_since_war"].mean() if "pct_increase_since_war" in df_gas.columns else 0

kpi1.metric("Peak Brent Crude", f"${brent_max:.2f}", "Max recorded")
kpi2.metric("Peak WTI Crude",   f"${wti_max:.2f}",   "Max recorded")
kpi3.metric("Max State Gas Price", f"${gas_max:.3f}/gal", "Post-war high")
kpi4.metric("Avg Gas Price Increase", f"{avg_pct_inc:.1f}%", "Since war start")
kpi5.metric("Hormuz Ships Δ", f"{ships_pct:.1f}%", f"Before: {int(ships_before):,} → After: {int(ships_after):,}")

st.markdown("---")

# ── Oil Price Timeline ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Crude Oil Price Timeline</div>', unsafe_allow_html=True)

if oil_metrics:
    fig_oil = go.Figure()

    color_map = {"brent_usd_barrel": "#e63946", "wti_usd_barrel": "#f4a261", "dubai_usd_barrel": "#2a9d8f"}
    label_map = {"brent_usd_barrel": "Brent", "wti_usd_barrel": "WTI", "dubai_usd_barrel": "Dubai"}

    for metric in oil_metrics:
        if metric in df_filtered.columns:
            fig_oil.add_trace(go.Scatter(
                x=df_filtered["date"],
                y=df_filtered[metric],
                name=label_map.get(metric, metric),
                line=dict(color=color_map.get(metric, "#888"), width=2),
                mode="lines",
                hovertemplate=f"<b>{label_map.get(metric)}</b>: $%{{y:.2f}}<br>Date: %{{x|%b %d, %Y}}<extra></extra>",
            ))

    # War start line
    fig_oil.add_shape(type="line",
        x0=WAR_DATE_STR, x1=WAR_DATE_STR, y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color="#ef4444", width=2, dash="dash")
    )
    fig_oil.add_annotation(
        x=WAR_DATE_STR, y=1, xref="x", yref="paper",
        text="War Start", showarrow=False,
        font=dict(color="#ef4444", size=11),
        xanchor="left", yanchor="top"
    )

    # Key events
    if not df_key.empty and "event" in df_key.columns:
        for _, row in df_key.iterrows():
            if pd.Timestamp(date_range[0]) <= row["date"] <= pd.Timestamp(date_range[1]):
                fig_oil.add_shape(type="line",
                    x0=row["date"].strftime("%Y-%m-%d"), x1=row["date"].strftime("%Y-%m-%d"),
                    y0=0, y1=1, xref="x", yref="paper",
                    line=dict(color="#94a3b8", width=1, dash="dot")
                )

    fig_oil.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="USD / Barrel",
        legend=dict(orientation="h", y=1.12),
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        hovermode="x unified",
    )
    st.plotly_chart(fig_oil, use_container_width=True)
else:
    st.info("Select at least one oil metric from the sidebar.")

# ── Strait of Hormuz + Gas Price ─────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="section-title">🚢 Strait of Hormuz – Daily Ships</div>', unsafe_allow_html=True)
    if "strait_hormuz_daily_ships" in df_filtered.columns:
        fig_ships = go.Figure()
        fig_ships.add_trace(go.Scatter(
            x=df_filtered["date"],
            y=df_filtered["strait_hormuz_daily_ships"],
            fill="tozeroy",
            line=dict(color="#38bdf8", width=2),
            fillcolor="rgba(56,189,248,0.15)",
            name="Daily Ships",
            hovertemplate="<b>Ships</b>: %{y}<br>%{x|%b %d}<extra></extra>",
        ))
        fig_ships.add_shape(type="line", x0=WAR_DATE_STR, x1=WAR_DATE_STR, y0=0, y1=1, xref="x", yref="paper", line=dict(color="#ef4444", width=2, dash="dash"))
        fig_ships.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="Ships / Day",
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_ships, use_container_width=True)

with col_right:
    st.markdown('<div class="section-title">⛽ Average Gas Price by Region</div>', unsafe_allow_html=True)
    if "region" in df_gas.columns and "gas_price_prewar_feb27" in df_gas.columns:
        region_avg = df_gas.groupby("region")[["gas_price_prewar_feb27", "gas_price_mar19_2026"]].mean().reset_index()
        region_avg.columns = ["Region", "Pre-War", "Post-War"]
        fig_reg = go.Figure()
        fig_reg.add_bar(x=region_avg["Region"], y=region_avg["Pre-War"],  name="Pre-War",  marker_color="#4ade80")
        fig_reg.add_bar(x=region_avg["Region"], y=region_avg["Post-War"], name="Post-War", marker_color="#f87171")
        fig_reg.update_layout(
            barmode="group",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="$/Gallon",
            legend=dict(orientation="h", y=1.12),
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_reg, use_container_width=True)

st.markdown("---")

# ── Phase Analysis ────────────────────────────────────────────────────────────
col_phase, col_heatmap = st.columns(2)

with col_phase:
    st.markdown('<div class="section-title">📊 Oil Prices by War Phase</div>', unsafe_allow_html=True)
    if "phase" in df_oil.columns:
        phase_avg = df_oil.groupby("phase")[["brent_usd_barrel", "wti_usd_barrel", "dubai_usd_barrel"]].mean().round(2).reset_index()
        phase_avg.columns = ["Phase", "Brent", "WTI", "Dubai"]
        fig_phase = px.bar(
            phase_avg.melt(id_vars="Phase", var_name="Type", value_name="Price"),
            x="Phase", y="Price", color="Type", barmode="group",
            color_discrete_map={"Brent": "#e63946", "WTI": "#f4a261", "Dubai": "#2a9d8f"},
            template="plotly_dark",
        )
        fig_phase.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=1.12),
        )
        st.plotly_chart(fig_phase, use_container_width=True)

with col_heatmap:
    st.markdown('<div class="section-title">🔥 % Gas Price Increase by Region</div>', unsafe_allow_html=True)
    if "region" in df_gas.columns and "pct_increase_since_war" in df_gas.columns:
        pct_region = df_gas.groupby("region")["pct_increase_since_war"].mean().reset_index()
        pct_region.columns = ["Region", "Avg % Increase"]
        fig_pct = px.bar(
            pct_region.sort_values("Avg % Increase", ascending=True),
            x="Avg % Increase", y="Region", orientation="h",
            color="Avg % Increase",
            color_continuous_scale=["#4ade80", "#fbbf24", "#ef4444"],
            template="plotly_dark",
        )
        fig_pct.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_pct, use_container_width=True)

st.markdown("---")

# ── State Map / Table ─────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🗺️ State-wise Gas Price Analysis</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📋 Data Table", "📊 Top 10 States"])

with tab1:
    display_cols = [c for c in ["state", "region", "gas_price_prewar_feb27", "gas_price_mar19_2026", "price_increase_since_war", "pct_increase_since_war"] if c in df_gas.columns]
    st.dataframe(
        df_gas[display_cols].sort_values("pct_increase_since_war", ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=350,
    )

with tab2:
    if "state" in df_gas.columns and "pct_increase_since_war" in df_gas.columns:
        top10 = df_gas.nlargest(10, "pct_increase_since_war")[["state", "gas_price_prewar_feb27", "gas_price_mar19_2026", "pct_increase_since_war"]]
        fig_top = px.bar(
            top10.sort_values("pct_increase_since_war"),
            x="pct_increase_since_war", y="state", orientation="h",
            color="pct_increase_since_war",
            color_continuous_scale=["#fbbf24", "#ef4444"],
            labels={"pct_increase_since_war": "% Increase", "state": "State"},
            template="plotly_dark",
        )
        fig_top.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_top, use_container_width=True)

st.markdown("---")

# ── Correlation Matrix ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🔗 Correlation: Oil Prices vs Ship Traffic</div>', unsafe_allow_html=True)

corr_cols = [c for c in ["brent_usd_barrel", "wti_usd_barrel", "dubai_usd_barrel", "strait_hormuz_daily_ships"] if c in df_oil.columns]
if len(corr_cols) > 1:
    corr = df_oil[corr_cols].corr().round(2)
    labels = [c.replace("_usd_barrel", "").replace("_", " ").title() for c in corr_cols]
    fig_corr = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=labels, y=labels,
        colorscale="RdBu",
        zmid=0,
        text=corr.values.round(2),
        texttemplate="%{text}",
        textfont_size=13,
        hovertemplate="%{y} × %{x}: %{z}<extra></extra>",
    ))
    fig_corr.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_corr, use_container_width=True)

# ── Key Events Timeline ───────────────────────────────────────────────────────
if not df_key.empty and "event" in df_key.columns:
    st.markdown("---")
    st.markdown('<div class="section-title">📅 Key Events Timeline</div>', unsafe_allow_html=True)
    st.dataframe(
        df_key[["date", "event"] + [c for c in df_key.columns if c not in ["date", "event"]]].sort_values("date"),
        use_container_width=True, height=250,
    )

st.markdown("---")
st.caption("🛢️ Iran War Energy Dashboard · Built with Streamlit + Plotly · Data for educational/research purposes only.")