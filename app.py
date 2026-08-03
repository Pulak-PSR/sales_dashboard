"""Interactive sales dashboard (Streamlit + Plotly) over a synthetic e-commerce dataset."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_generator import generate_data

# ----------------------------------------------------------------------------
# Palette (dark, professional) — see README for source
# ----------------------------------------------------------------------------
SURFACE = "#1a1a19"
PAGE = "#0d0d0d"
INK_PRIMARY = "#ffffff"
INK_SECONDARY = "#c3c2b7"
INK_MUTED = "#898781"
GRIDLINE = "#2c2c2a"
BASELINE = "#383835"

BLUE = "#3987e5"
ORANGE = "#d95926"
AQUA = "#199e70"
YELLOW = "#c98500"
GOOD = "#0ca30c"

REGION_COLORS = {
    "East": BLUE,
    "North": YELLOW,
    "South": AQUA,
    "West": ORANGE,
}

SEQ_BLUE = ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"]

st.set_page_config(
    page_title="Sales Performance Dashboard",
    page_icon="\U0001F4CA",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {PAGE}; }}
    section[data-testid="stSidebar"] {{ background-color: {SURFACE}; }}
    h1, h2, h3, p, span, label {{ color: {INK_PRIMARY}; }}
    .kpi-card {{
        background-color: {SURFACE};
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 10px;
        padding: 18px 20px;
    }}
    .kpi-label {{
        color: {INK_MUTED};
        font-size: 0.82rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        color: {INK_PRIMARY};
        font-size: 1.8rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }}
    .kpi-delta {{
        color: {GOOD};
        font-size: 0.8rem;
        margin-top: 4px;
    }}
    .section-title {{
        color: {INK_PRIMARY};
        font-size: 1.05rem;
        font-weight: 600;
        margin: 6px 0 2px 0;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def dark_template() -> go.layout.Template:
    return go.layout.Template(
        layout=go.Layout(
            paper_bgcolor=SURFACE,
            plot_bgcolor=SURFACE,
            font=dict(color=INK_SECONDARY, family="Segoe UI, system-ui, sans-serif", size=13),
            title=dict(font=dict(color=INK_PRIMARY, size=15)),
            xaxis=dict(gridcolor=GRIDLINE, linecolor=BASELINE, zerolinecolor=BASELINE, tickfont=dict(color=INK_MUTED)),
            yaxis=dict(gridcolor=GRIDLINE, linecolor=BASELINE, zerolinecolor=BASELINE, tickfont=dict(color=INK_MUTED)),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=INK_SECONDARY)),
            margin=dict(l=10, r=10, t=40, b=10),
            hoverlabel=dict(bgcolor=PAGE, font=dict(color=INK_PRIMARY)),
        )
    )


TEMPLATE = dark_template()


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    df = generate_data()
    df["Date"] = pd.to_datetime(df["Date"])
    return df


df = load_data()

# ----------------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------------
st.sidebar.markdown("## Filters")

min_date, max_date = df["Date"].min().date(), df["Date"].max().date()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

regions = st.sidebar.multiselect(
    "Region", options=sorted(df["Region"].unique()), default=sorted(df["Region"].unique())
)
categories = st.sidebar.multiselect(
    "Product Category",
    options=sorted(df["Product Category"].unique()),
    default=sorted(df["Product Category"].unique()),
)

mask = (
    (df["Date"].dt.date >= start_date)
    & (df["Date"].dt.date <= end_date)
    & (df["Region"].isin(regions))
    & (df["Product Category"].isin(categories))
)
fdf = df.loc[mask]

st.sidebar.markdown("---")
st.sidebar.caption(f"{len(fdf):,} of {len(df):,} orders match current filters.")

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown("# Sales Performance Dashboard")
st.markdown(
    f'<span style="color:{INK_MUTED}">Synthetic e-commerce dataset · '
    f'{min_date:%b %Y} – {max_date:%b %Y}</span>',
    unsafe_allow_html=True,
)
st.write("")

if fdf.empty:
    st.warning("No orders match the selected filters.")
    st.stop()

# ----------------------------------------------------------------------------
# KPI cards
# ----------------------------------------------------------------------------
total_revenue = fdf["Sales"].sum()
total_profit = fdf["Profit"].sum()
total_orders = fdf["Order ID"].nunique()
avg_order_value = total_revenue / total_orders if total_orders else 0
margin_pct = (total_profit / total_revenue * 100) if total_revenue else 0

kpis = [
    ("Total Revenue", f"${total_revenue:,.0f}"),
    ("Total Profit", f"${total_profit:,.0f}"),
    ("Average Order Value", f"${avg_order_value:,.2f}"),
    ("Total Orders", f"{total_orders:,}"),
]

cols = st.columns(4)
for col, (label, value) in zip(cols, kpis):
    col.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    f'<div class="kpi-delta" style="margin-top:8px;">Overall profit margin: {margin_pct:.1f}%</div>',
    unsafe_allow_html=True,
)
st.write("")

# ----------------------------------------------------------------------------
# Monthly revenue trend
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">Monthly Revenue Trend</div>', unsafe_allow_html=True)

monthly = (
    fdf.set_index("Date")
    .resample("MS")["Sales"]
    .sum()
    .reset_index()
    .rename(columns={"Date": "Month", "Sales": "Revenue"})
)

line_fig = go.Figure()
line_fig.add_trace(
    go.Scatter(
        x=monthly["Month"],
        y=monthly["Revenue"],
        mode="lines",
        line=dict(color=BLUE, width=2, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(57,135,229,0.12)",
        hovertemplate="%{x|%b %Y}<br>Revenue: $%{y:,.0f}<extra></extra>",
    )
)
line_fig.update_layout(template=TEMPLATE, height=340, hovermode="x unified")
line_fig.update_yaxes(title=None, tickprefix="$", tickformat=",.0f")
line_fig.update_xaxes(title=None)
st.plotly_chart(line_fig, width="stretch", config={"displayModeBar": False})

# ----------------------------------------------------------------------------
# Sales by category (bar) + Regional distribution (pie)
# ----------------------------------------------------------------------------
left, right = st.columns([3, 2])

with left:
    st.markdown('<div class="section-title">Sales by Category</div>', unsafe_allow_html=True)
    cat_sales = (
        fdf.groupby("Product Category", as_index=False)["Sales"].sum().sort_values("Sales", ascending=True)
    )
    bar_fig = go.Figure(
        go.Bar(
            x=cat_sales["Sales"],
            y=cat_sales["Product Category"],
            orientation="h",
            marker=dict(color=BLUE, line=dict(width=0)),
            hovertemplate="%{y}<br>Sales: $%{x:,.0f}<extra></extra>",
        )
    )
    bar_fig.update_layout(template=TEMPLATE, height=340)
    bar_fig.update_xaxes(title=None, tickprefix="$", tickformat=",.0f")
    bar_fig.update_yaxes(title=None)
    st.plotly_chart(bar_fig, width="stretch", config={"displayModeBar": False})

with right:
    st.markdown('<div class="section-title">Regional Distribution</div>', unsafe_allow_html=True)
    region_sales = fdf.groupby("Region", as_index=False)["Sales"].sum()
    region_order = ["East", "North", "South", "West"]
    region_sales = region_sales.set_index("Region").reindex(region_order).dropna().reset_index()
    pie_fig = go.Figure(
        go.Pie(
            labels=region_sales["Region"],
            values=region_sales["Sales"],
            hole=0.55,
            sort=False,
            marker=dict(colors=[REGION_COLORS[r] for r in region_sales["Region"]], line=dict(color=SURFACE, width=2)),
            textinfo="label+percent",
            textfont=dict(color=INK_PRIMARY, size=12),
            hovertemplate="%{label}<br>Sales: $%{value:,.0f}<extra></extra>",
        )
    )
    pie_fig.update_layout(template=TEMPLATE, height=340, showlegend=False)
    st.plotly_chart(pie_fig, width="stretch", config={"displayModeBar": False})

# ----------------------------------------------------------------------------
# Top 10 products by profit (heatmap-style table)
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">Top 10 Products by Profit</div>', unsafe_allow_html=True)

top_products = (
    fdf.groupby("Product Name", as_index=False)
    .agg(Profit=("Profit", "sum"), Sales=("Sales", "sum"), Orders=("Order ID", "nunique"))
    .sort_values("Profit", ascending=False)
    .head(10)
    .sort_values("Profit", ascending=True)
)

heat_fig = go.Figure(
    go.Bar(
        x=top_products["Profit"],
        y=top_products["Product Name"],
        orientation="h",
        marker=dict(
            color=top_products["Profit"],
            colorscale=[[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)],
            line=dict(width=0),
        ),
        text=[f"${v:,.0f}" for v in top_products["Profit"]],
        textposition="outside",
        textfont=dict(color=INK_SECONDARY),
        hovertemplate="%{y}<br>Profit: $%{x:,.0f}<extra></extra>",
    )
)
heat_fig.update_layout(template=TEMPLATE, height=420)
heat_fig.update_xaxes(title=None, tickprefix="$", tickformat=",.0f")
heat_fig.update_yaxes(title=None)
st.plotly_chart(heat_fig, width="stretch", config={"displayModeBar": False})

with st.expander("View as table"):
    display_df = top_products.sort_values("Profit", ascending=False).reset_index(drop=True)
    display_df.index += 1
    st.dataframe(
        display_df.style.format({"Profit": "${:,.0f}", "Sales": "${:,.0f}"}),
        width="stretch",
    )
