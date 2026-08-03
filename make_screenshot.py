"""Composite a dashboard-preview PNG from the app's actual chart code + data.

Not a browser screenshot (headless capture wasn't available in this
environment) — it renders the same Plotly figures the app produces, from the
same synthetic data, and lays them out to mirror the live Streamlit page.
Run manually if the dataset or chart code changes: python make_screenshot.py
"""

from __future__ import annotations

import io

import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont

from app import (
    BLUE,
    GOOD,
    GRIDLINE,
    INK_MUTED,
    INK_PRIMARY,
    INK_SECONDARY,
    PAGE,
    REGION_COLORS,
    SEQ_BLUE,
    SURFACE,
    dark_template,
)
from data_generator import generate_data

W = 1600
SCALE = 2

df = generate_data()
TEMPLATE = dark_template()

SIDEBAR_W = 280
CONTENT_X = SIDEBAR_W + 40
CONTENT_W = W - CONTENT_X - 40


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def render_fig(fig: go.Figure, width: int, height: int) -> Image.Image:
    fig.update_layout(template=TEMPLATE, width=width, height=height)
    png_bytes = fig.to_image(format="png", scale=SCALE)
    return Image.open(io.BytesIO(png_bytes))


# ---- charts (mirrors app.py) -------------------------------------------------
monthly = (
    df.set_index("Date").resample("MS")["Sales"].sum().reset_index()
    .rename(columns={"Date": "Month", "Sales": "Revenue"})
)
line_fig = go.Figure()
line_fig.add_trace(
    go.Scatter(
        x=monthly["Month"], y=monthly["Revenue"], mode="lines",
        line=dict(color=BLUE, width=2, shape="spline"),
        fill="tozeroy", fillcolor="rgba(57,135,229,0.12)",
    )
)
line_fig.update_layout(margin=dict(l=60, r=20, t=10, b=30))
line_fig.update_yaxes(tickprefix="$", tickformat=",.0f")

cat_sales = df.groupby("Product Category", as_index=False)["Sales"].sum().sort_values("Sales")
bar_fig = go.Figure(
    go.Bar(x=cat_sales["Sales"], y=cat_sales["Product Category"], orientation="h", marker=dict(color=BLUE))
)
bar_fig.update_layout(margin=dict(l=140, r=20, t=10, b=30))
bar_fig.update_xaxes(tickprefix="$", tickformat=",.0f")
bar_fig.update_yaxes(automargin=True)

region_sales = df.groupby("Region", as_index=False)["Sales"].sum()
region_order = ["East", "North", "South", "West"]
region_sales = region_sales.set_index("Region").reindex(region_order).reset_index()
pie_fig = go.Figure(
    go.Pie(
        labels=region_sales["Region"], values=region_sales["Sales"], hole=0.55, sort=False,
        marker=dict(colors=[REGION_COLORS[r] for r in region_sales["Region"]], line=dict(color=SURFACE, width=2)),
        textinfo="label+percent", textfont=dict(color=INK_PRIMARY, size=13),
        textposition="outside",
    )
)
pie_fig.update_layout(showlegend=False, margin=dict(l=40, r=40, t=20, b=20))

top_products = (
    df.groupby("Product Name", as_index=False)
    .agg(Profit=("Profit", "sum"))
    .sort_values("Profit", ascending=False).head(10).sort_values("Profit")
)
heat_fig = go.Figure(
    go.Bar(
        x=top_products["Profit"], y=top_products["Product Name"], orientation="h",
        marker=dict(color=top_products["Profit"], colorscale=[[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)]),
        text=[f"${v:,.0f}" for v in top_products["Profit"]], textposition="outside",
        textfont=dict(color=INK_SECONDARY),
        cliponaxis=False,
    )
)
heat_fig.update_layout(margin=dict(l=200, r=70, t=10, b=30))
heat_fig.update_xaxes(tickprefix="$", tickformat=",.0f", range=[0, top_products["Profit"].max() * 1.15])
heat_fig.update_yaxes(automargin=True)

LINE_W, LINE_H = CONTENT_W - 8, 372
BAR_W, PIE_W, ROW2_H = 800, CONTENT_W - 800 - 20 - 8, 372
HEAT_W, HEAT_H = CONTENT_W - 8, 452

line_img = render_fig(line_fig, LINE_W, LINE_H)
bar_img = render_fig(bar_fig, BAR_W, ROW2_H)
pie_img = render_fig(pie_fig, PIE_W, ROW2_H)
heat_img = render_fig(heat_fig, HEAT_W, HEAT_H)

# ---- compose full-page mockup ------------------------------------------------
H = 1660
canvas = Image.new("RGB", (W * SCALE, H * SCALE), PAGE)
draw = ImageDraw.Draw(canvas)


def s(v: int) -> int:
    return v * SCALE


def card(x, y, w, h, fill=SURFACE, outline="#3a3a38"):
    draw.rounded_rectangle([s(x), s(y), s(x + w), s(y + h)], radius=s(10), fill=fill, outline=outline, width=SCALE)


def pill(x, y, text, txt_font, accent=BLUE):
    pad_x, pad_y = 10, 6
    tw = draw.textlength(text, font=txt_font)
    w, h = int(tw) + pad_x * 2, txt_font.size + pad_y * 2
    draw.rounded_rectangle([s(x), s(y), s(x + w), s(y + h)], radius=s(h // 2), fill="#262623", outline=accent, width=SCALE)
    draw.text((s(x + pad_x), s(y + pad_y - 1)), text, font=txt_font, fill=INK_PRIMARY)
    return w


def pill_row(x, y, items, txt_font, max_w, accent=BLUE, gap=8, line_gap=8):
    cx, cy = x, y
    for item in items:
        w = pill(cx, cy, item, txt_font, accent)
        cx += w + gap
        if cx - x > max_w - 60:
            cx = x
            cy += txt_font.size + 6 + 2 + line_gap
    return cy + txt_font.size + 6 + 2


title_font = font(30 * SCALE, bold=True)
sub_font = font(15 * SCALE)
section_font = font(17 * SCALE, bold=True)
kpi_label_font = font(13 * SCALE, bold=True)
kpi_value_font = font(28 * SCALE, bold=True)
label_font = font(15 * SCALE, bold=True)
pill_font = font(13 * SCALE)
muted_font = font(13 * SCALE)

# sidebar
draw.rectangle([0, 0, s(SIDEBAR_W), H * SCALE], fill=SURFACE)
draw.line([s(SIDEBAR_W), 0, s(SIDEBAR_W), H * SCALE], fill=GRIDLINE, width=SCALE)
sx = 24
sy = 24
draw.text((s(sx), s(sy)), "Filters", font=font(20 * SCALE, bold=True), fill=INK_PRIMARY)
sy += 44

draw.text((s(sx), s(sy)), "Date range", font=label_font, fill=INK_PRIMARY)
sy += 26
draw.text((s(sx), s(sy)), "2022-01-01  →  2025-12-31", font=muted_font, fill=INK_MUTED)
sy += 38

draw.text((s(sx), s(sy)), "Region", font=label_font, fill=INK_PRIMARY)
sy += 28
sy = pill_row(sx, sy, ["East", "North", "South", "West"], pill_font, SIDEBAR_W - sx, accent=BLUE)
sy += 20

draw.text((s(sx), s(sy)), "Product Category", font=label_font, fill=INK_PRIMARY)
sy += 28
sy = pill_row(
    sx, sy,
    ["Clothing", "Furniture", "Health & Beauty", "Office Supplies", "Sporting Goods", "Technology"],
    pill_font, SIDEBAR_W - sx, accent=BLUE,
)
sy += 24

draw.line([s(sx), s(sy), s(SIDEBAR_W - sx), s(sy)], fill=GRIDLINE, width=SCALE)
sy += 16
draw.text((s(sx), s(sy)), "15,000 of 15,000 orders", font=muted_font, fill=INK_MUTED)
sy += 18
draw.text((s(sx), s(sy)), "match current filters.", font=muted_font, fill=INK_MUTED)

# header
draw.text((s(CONTENT_X), s(30)), "Sales Performance Dashboard", font=title_font, fill=INK_PRIMARY)
draw.text((s(CONTENT_X), s(74)), "Synthetic e-commerce dataset · Jan 2022 – Dec 2025", font=sub_font, fill=INK_MUTED)

# KPI cards
total_revenue = df["Sales"].sum()
total_profit = df["Profit"].sum()
total_orders = df["Order ID"].nunique()
avg_order_value = total_revenue / total_orders
margin_pct = total_profit / total_revenue * 100

kpis = [
    ("TOTAL REVENUE", f"${total_revenue:,.0f}"),
    ("TOTAL PROFIT", f"${total_profit:,.0f}"),
    ("AVERAGE ORDER VALUE", f"${avg_order_value:,.2f}"),
    ("TOTAL ORDERS", f"{total_orders:,}"),
]
kpi_y = 115
kpi_w = (CONTENT_W - 3 * 16) // 4
for i, (label, value) in enumerate(kpis):
    x = CONTENT_X + i * (kpi_w + 16)
    card(x, kpi_y, kpi_w, 90)
    draw.text((s(x + 18), s(kpi_y + 16)), label, font=kpi_label_font, fill=INK_MUTED)
    draw.text((s(x + 18), s(kpi_y + 40)), value, font=kpi_value_font, fill=INK_PRIMARY)
draw.text((s(CONTENT_X), s(kpi_y + 100)), f"Overall profit margin: {margin_pct:.1f}%", font=font(13 * SCALE), fill=GOOD)

# monthly trend
sec_y = kpi_y + 140
draw.text((s(CONTENT_X), s(sec_y)), "Monthly Revenue Trend", font=section_font, fill=INK_PRIMARY)
card(CONTENT_X, sec_y + 28, CONTENT_W, LINE_H + 8)
canvas.paste(line_img.convert("RGB"), (s(CONTENT_X + 4), s(sec_y + 32)))

# bar + pie row
row2_y = sec_y + 28 + LINE_H + 8 + 30
draw.text((s(CONTENT_X), s(row2_y)), "Sales by Category", font=section_font, fill=INK_PRIMARY)
draw.text((s(CONTENT_X + BAR_W + 20), s(row2_y)), "Regional Distribution", font=section_font, fill=INK_PRIMARY)
card(CONTENT_X, row2_y + 28, BAR_W, ROW2_H + 8)
card(CONTENT_X + BAR_W + 20, row2_y + 28, PIE_W, ROW2_H + 8)
canvas.paste(bar_img.convert("RGB"), (s(CONTENT_X + 4), s(row2_y + 32)))
canvas.paste(pie_img.convert("RGB"), (s(CONTENT_X + BAR_W + 24), s(row2_y + 32)))

# top products
row3_y = row2_y + 28 + ROW2_H + 8 + 30
draw.text((s(CONTENT_X), s(row3_y)), "Top 10 Products by Profit", font=section_font, fill=INK_PRIMARY)
card(CONTENT_X, row3_y + 28, CONTENT_W, HEAT_H + 8)
canvas.paste(heat_img.convert("RGB"), (s(CONTENT_X + 4), s(row3_y + 32)))

H = row3_y + 28 + HEAT_H + 8 + 30
canvas = canvas.crop((0, 0, W * SCALE, s(H)))
canvas = canvas.resize((W, H), Image.LANCZOS)
canvas.save("assets/screenshot.png")
print("Wrote assets/screenshot.png")
