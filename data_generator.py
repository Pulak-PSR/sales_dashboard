"""Synthetic e-commerce sales dataset generator.

Produces ~15,000 order-line rows resembling a Superstore-style dataset:
Order ID, Date, Customer Segment, Product Category, Region, Sales, Profit, Quantity.

Run directly to write data/sales_data.csv:
    python data_generator.py
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

N_ROWS = 15_000
SEED = 42

START_DATE = pd.Timestamp("2022-01-01")
END_DATE = pd.Timestamp("2025-12-31")

REGIONS = ["East", "West", "South", "North"]
SEGMENTS = ["Consumer", "Corporate", "Home Office"]

# Category -> (products, unit price range, base margin range)
CATEGORIES: dict[str, dict] = {
    "Furniture": {
        "products": [
            "Executive Office Chair", "Adjustable Standing Desk", "Bookcase - 5 Shelf",
            "Conference Table", "Ergonomic Mesh Chair", "Filing Cabinet",
            "Sofa - 3 Seater", "Study Desk", "Bunk Bed Frame", "Dining Table Set",
        ],
        "price_range": (60, 1200),
        "margin_range": (-0.15, 0.20),
    },
    "Office Supplies": {
        "products": [
            "Sticky Notes Pack", "Ballpoint Pen Box", "Copy Paper Ream",
            "Stapler Heavy Duty", "Binder Clips Set", "Desk Organizer",
            "Whiteboard Markers", "Envelopes Box", "Shredder", "Label Printer",
        ],
        "price_range": (3, 250),
        "margin_range": (0.05, 0.35),
    },
    "Technology": {
        "products": [
            "Wireless Mouse", "27-inch Monitor", "Mechanical Keyboard",
            "Noise Cancelling Headphones", "Laptop Stand", "USB-C Docking Station",
            "Business Laptop", "Smartphone", "Bluetooth Speaker", "Webcam HD",
        ],
        "price_range": (15, 1800),
        "margin_range": (0.02, 0.30),
    },
    "Clothing": {
        "products": [
            "Cotton T-Shirt", "Denim Jacket", "Running Shoes", "Wool Sweater",
            "Rain Jacket", "Formal Trousers", "Baseball Cap", "Winter Coat",
        ],
        "price_range": (10, 220),
        "margin_range": (0.10, 0.45),
    },
    "Health & Beauty": {
        "products": [
            "Electric Toothbrush", "Skincare Set", "Hair Dryer", "Vitamin Supplements",
            "Perfume", "Massage Gun", "Yoga Mat", "Digital Scale",
        ],
        "price_range": (8, 300),
        "margin_range": (0.05, 0.40),
    },
    "Sporting Goods": {
        "products": [
            "Basketball", "Dumbbell Set", "Tennis Racket", "Camping Tent",
            "Cycling Helmet", "Fitness Tracker", "Golf Club Set", "Hiking Backpack",
        ],
        "price_range": (12, 600),
        "margin_range": (0.05, 0.30),
    },
}

def generate_data(n_rows: int = N_ROWS, seed: int = SEED) -> pd.DataFrame:
    """Return a synthetic sales DataFrame with n_rows order lines."""
    local_rng = np.random.default_rng(seed)

    categories = list(CATEGORIES.keys())
    category_choices = local_rng.choice(categories, size=n_rows)

    rows = []
    dates = START_DATE + pd.to_timedelta(
        local_rng.integers(0, (END_DATE - START_DATE).days + 1, size=n_rows), unit="D"
    )
    regions = local_rng.choice(REGIONS, size=n_rows)
    segments = local_rng.choice(SEGMENTS, size=n_rows, p=[0.55, 0.30, 0.15])
    quantities = local_rng.integers(1, 9, size=n_rows)

    for i in range(n_rows):
        cat = category_choices[i]
        spec = CATEGORIES[cat]
        product = local_rng.choice(spec["products"])
        unit_price = local_rng.uniform(*spec["price_range"])
        qty = int(quantities[i])
        discount = local_rng.choice([0, 0, 0, 0.1, 0.15, 0.2, 0.3], p=[0.45, 0.1, 0.1, 0.15, 0.1, 0.05, 0.05])
        sales = round(unit_price * qty * (1 - discount), 2)
        margin = local_rng.uniform(*spec["margin_range"])
        profit = round(sales * margin, 2)

        rows.append(
            {
                "Order ID": f"ORD-{100000 + i}",
                "Date": dates[i],
                "Customer Segment": segments[i],
                "Product Category": cat,
                "Product Name": product,
                "Region": regions[i],
                "Sales": sales,
                "Profit": profit,
                "Quantity": qty,
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values("Date").reset_index(drop=True)
    return df


def main() -> None:
    df = generate_data()
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sales_data.csv")
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df):,} rows to {out_path}")


if __name__ == "__main__":
    main()
