"""
Amazon Sales Dashboard — Backend (Simplified Teaching Version, restyled v2)
================================================================
This file has 5 sections:
  0. COLOR CONFIG + set_theme() (one place to change the whole theme)
  1. Load data
  2. Clean data
  3. Add useful columns (feature engineering)
  4. Make charts

NOTE: All data logic is unchanged. Only colors / chart appearance changed.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter
from collections import Counter
from itertools import combinations

# ===========================================================================
# 0. COLOR CONFIG
#    The frontend has a Dark-mode switch and a Color-theme picker in the
#    sidebar; both call set_theme(). THEME / ACCENT are only the defaults.
# ===========================================================================

THEME = "dark"      # default mode: "dark" or "light"
ACCENT = "Indigo"   # default color family: any key of ACCENTS below

# Neutrals: backgrounds, text, gridlines. Shared by every accent.
NEUTRALS = {
    "light": {
        "bg": "#F4F6FB", "sidebar": "#FFFFFF", "card": "#FFFFFF", "border": "#E3E8F0",
        "text": "#1E293B", "muted": "#64748B", "axis_text": "#334155", "grid": "#E5E9F0",
        "positive": "#16A34A", "negative": "#DC2626",
        "shadow": "0 1px 3px rgba(15,23,42,0.08), 0 4px 12px rgba(15,23,42,0.06)",
        "shadow_hover": "0 8px 24px rgba(15,23,42,0.16)",
    },
    "dark": {
        "bg": "#0B1220", "sidebar": "#0F172A", "card": "#151E33", "border": "#26334D",
        "text": "#F1F5F9", "muted": "#94A3B8", "axis_text": "#CBD5E1", "grid": "#26334D",
        "positive": "#4ADE80", "negative": "#F87171",
        "shadow": "0 1px 3px rgba(0,0,0,0.4), 0 4px 12px rgba(0,0,0,0.3)",
        "shadow_hover": "0 8px 24px rgba(0,0,0,0.55)",
    },
}


def _accent(primary, hover, disabled, soft, on_primary, hero_from, hero_to,
            bar_low, bar_high, contrast, series):
    """One accent color set: buttons, header gradient, bar gradient, line colors."""
    return {
        "primary": primary,            # buttons, line charts
        "primary_hover": hover,        # button hover
        "primary_disabled": disabled,  # button disabled
        "primary_soft": soft,          # soft tint (upload zone, tags, alerts)
        "on_primary": on_primary,      # text drawn on the primary color
        "hero_from": hero_from,        # header gradient start
        "hero_to": hero_to,            # header gradient end
        "bar_low": bar_low,            # bar gradient: smallest value
        "bar_high": bar_high,          # bar gradient: biggest value
        "contrast": contrast,          # 2nd color (histogram curve)
        "series": series,              # 6-color sequence for multi-series charts
    }


# Every accent has a light and a dark version. Add your own by copying one.
ACCENTS = {
    "Indigo": {
        "light": _accent("#4F46E5", "#4338CA", "#A5B4FC", "#EEF2FF", "#FFFFFF",
                         "#4F46E5", "#7C3AED", "#A5B4FC", "#4338CA", "#F59E0B",
                         ["#4F46E5", "#0EA5E9", "#14B8A6", "#F59E0B", "#EC4899", "#8B5CF6"]),
        "dark":  _accent("#818CF8", "#A5B4FC", "#3B4470", "#1B2545", "#0B1220",
                         "#3730A3", "#6D28D9", "#4F46E5", "#C7D2FE", "#FBBF24",
                         ["#818CF8", "#38BDF8", "#2DD4BF", "#FBBF24", "#F472B6", "#A78BFA"]),
    },
    "Emerald": {
        "light": _accent("#059669", "#047857", "#6EE7B7", "#ECFDF5", "#FFFFFF",
                         "#059669", "#0D9488", "#6EE7B7", "#047857", "#F59E0B",
                         ["#059669", "#0EA5E9", "#F59E0B", "#8B5CF6", "#EC4899", "#64748B"]),
        "dark":  _accent("#34D399", "#6EE7B7", "#1F4D42", "#10302B", "#04150F",
                         "#065F46", "#0F766E", "#047857", "#A7F3D0", "#FBBF24",
                         ["#34D399", "#38BDF8", "#FBBF24", "#A78BFA", "#F472B6", "#94A3B8"]),
    },
    "Ocean": {
        "light": _accent("#0284C7", "#0369A1", "#7DD3FC", "#F0F9FF", "#FFFFFF",
                         "#0284C7", "#2563EB", "#7DD3FC", "#0369A1", "#F59E0B",
                         ["#0284C7", "#14B8A6", "#F59E0B", "#8B5CF6", "#EC4899", "#64748B"]),
        "dark":  _accent("#38BDF8", "#7DD3FC", "#1E4A63", "#0F2A3F", "#04121C",
                         "#075985", "#1D4ED8", "#0369A1", "#BAE6FD", "#FBBF24",
                         ["#38BDF8", "#2DD4BF", "#FBBF24", "#A78BFA", "#F472B6", "#94A3B8"]),
    },
    "Sunset": {
        "light": _accent("#EA580C", "#C2410C", "#FDBA74", "#FFF7ED", "#FFFFFF",
                         "#F97316", "#E11D48", "#FDBA74", "#C2410C", "#0EA5E9",
                         ["#EA580C", "#0EA5E9", "#14B8A6", "#8B5CF6", "#EC4899", "#64748B"]),
        "dark":  _accent("#FB923C", "#FDBA74", "#5A3418", "#33200F", "#1A0C02",
                         "#C2410C", "#BE123C", "#C2410C", "#FED7AA", "#38BDF8",
                         ["#FB923C", "#38BDF8", "#2DD4BF", "#A78BFA", "#F472B6", "#94A3B8"]),
    },
    "Rose": {
        "light": _accent("#E11D48", "#BE123C", "#FDA4AF", "#FFF1F2", "#FFFFFF",
                         "#E11D48", "#9333EA", "#FDA4AF", "#BE123C", "#F59E0B",
                         ["#E11D48", "#0EA5E9", "#14B8A6", "#F59E0B", "#8B5CF6", "#64748B"]),
        "dark":  _accent("#FB7185", "#FDA4AF", "#5A1F2E", "#34141D", "#1F050B",
                         "#9F1239", "#7E22CE", "#BE123C", "#FECDD3", "#FBBF24",
                         ["#FB7185", "#38BDF8", "#2DD4BF", "#FBBF24", "#A78BFA", "#94A3B8"]),
    },
}

C = {}   # the ACTIVE palette. Filled by set_theme(); shared with the frontend.


def set_theme(mode="dark", accent="Indigo"):
    """Switch every chart (and the frontend, which reads C) to a mode + accent."""
    global THEME, ACCENT
    THEME = mode if mode in NEUTRALS else "dark"
    ACCENT = accent if accent in ACCENTS else "Indigo"
    C.clear()
    C.update(NEUTRALS[THEME])
    C.update(ACCENTS[ACCENT][THEME])

    sns.set_theme(
        style="whitegrid",
        rc={
            "figure.facecolor": C["card"],
            "axes.facecolor": C["card"],
            "savefig.facecolor": C["card"],
            "figure.dpi": 130,
            "savefig.dpi": 130,
            "axes.edgecolor": C["border"],
            "axes.labelcolor": C["axis_text"],
            "axes.titlecolor": C["text"],
            "text.color": C["text"],
            "xtick.color": C["axis_text"],
            "ytick.color": C["axis_text"],
            "xtick.labelsize": 10.5,
            "ytick.labelsize": 10.5,
            "grid.color": C["grid"],
            "grid.linewidth": 0.8,
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.titlepad": 14,
            "axes.labelsize": 11,
            "font.family": "sans-serif",
            "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
        },
    )


set_theme(THEME, ACCENT)

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ---------------------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------------------

def load_single_file(file):

    if file.name.endswith(".csv"):
        return pd.read_csv(file)

    elif file.name.endswith(".xlsx"):
        return pd.read_excel(file)

    else:
        return None


# ---------------------------------------------------------------------------
# 2. CLEAN DATA
# ---------------------------------------------------------------------------

def clean_data(df):
    """Remove blank rows, fix numeric columns, and calculate Sales."""
    df = df.copy()
    df.dropna(how="all", inplace=True)

    # Some exports repeat the header row in the middle of the data — remove it.
    if "Quantity Ordered" in df.columns:
        df = df[df["Quantity Ordered"] != "Quantity Ordered"]

    for col in ["Quantity Ordered", "Price Each"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    numeric_cols_present = [c for c in ["Quantity Ordered", "Price Each"] if c in df.columns]
    if numeric_cols_present:
        df.dropna(subset=numeric_cols_present, inplace=True)
    df.drop_duplicates(inplace=True)

    if "Sales" not in df.columns and "Quantity Ordered" in df.columns and "Price Each" in df.columns:
        df["Sales"] = df["Quantity Ordered"] * df["Price Each"]

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 3. ADD USEFUL COLUMNS
# ---------------------------------------------------------------------------

def feature_engineering(df):
    """Break 'Order Date' into separate Year / Month / Day / Hour columns."""
    df = df.copy()
    if "Order Date" in df.columns:
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
        df.dropna(subset=["Order Date"], inplace=True)
        df["Year"] = df["Order Date"].dt.year
        df["Month"] = df["Order Date"].dt.month
        df["MonthName"] = df["Month"].apply(lambda m: MONTH_NAMES[m - 1])
        df["DayName"] = df["Order Date"].dt.dayofweek.apply(lambda d: DAY_NAMES[d])
        df["Hour"] = df["Order Date"].dt.hour
    return df


def add_city_state_column(df, address_column="Purchase Address"):
    """Split '123 Main St, City, ST 00000' into 'City' and 'State' columns."""
    df = df.copy()
    if address_column not in df.columns:
        return df

    parts = df[address_column].str.split(",", expand=True)
    df["City"] = parts[1].str.strip()
    df["State"] = parts[2].str.strip().str.split(" ").str[0]
    return df


def get_kpis(df):
    """Return a small dict of headline numbers for the KPI cards."""
    return {
        "total_sales": df["Sales"].sum() if "Sales" in df else 0,
        "total_orders": df["Order ID"].nunique() if "Order ID" in df else len(df),
        "unique_products": df["Product"].nunique() if "Product" in df else 0,
        "avg_order_value": df["Sales"].mean() if "Sales" in df else 0,
        "top_product": df.groupby("Product")["Sales"].sum().idxmax() if "Product" in df and "Sales" in df else "N/A",
        "top_city": df.groupby("City")["Sales"].sum().idxmax() if "City" in df and "Sales" in df else "N/A",
    }


# ---------------------------------------------------------------------------
# 4. CHARTS — styling helpers first
# ---------------------------------------------------------------------------

def _money(x, _pos=None):
    """Axis format: 2500000 -> $2.5M, 45000 -> $45K."""
    if abs(x) >= 1_000_000:
        return f"${x / 1_000_000:.1f}M"
    if abs(x) >= 1_000:
        return f"${x / 1_000:.0f}K"
    return f"${x:,.0f}"


def _label_value(v, money):
    """Number printed on top of a bar / at a line's peak."""
    if money:
        if abs(v) >= 1_000_000:
            return f"${v / 1_000_000:.2f}M"
        if abs(v) >= 1_000:
            return f"${v / 1_000:.0f}K"
        return f"${v:,.0f}"
    return f"{v:,.0f}"


def _gradient(values):
    """Bar colors: small values = bar_low, big values = bar_high."""
    cmap = LinearSegmentedColormap.from_list("bars", [C["bar_low"], C["bar_high"]])
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    return [cmap((v - lo) / span) for v in values]


def _finish(fig, ax, title, xlabel=None, ylabel=None, grid_axis="y", money_axis=None):
    """Shared chart polish: title, labels, light grid, no top/right border."""
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel(xlabel or "")
    ax.set_ylabel(ylabel or "")
    ax.grid(False)
    ax.grid(axis=grid_axis, color=C["grid"], linewidth=0.8)
    ax.set_axisbelow(True)
    sns.despine(ax=ax, left=True, bottom=False)
    ax.tick_params(length=0)
    if money_axis == "y":
        ax.yaxis.set_major_formatter(FuncFormatter(_money))
    elif money_axis == "x":
        ax.xaxis.set_major_formatter(FuncFormatter(_money))
    fig.tight_layout()
    plt.close(fig)   # stops figures piling up in memory; st.pyplot still works
    return fig


def _draw_bars(ax, labels, values, horizontal, rotate, money):
    """Gradient bars with the value printed on each bar."""
    colors = _gradient(values)
    pos = list(range(len(values)))
    if horizontal:
        bars = ax.barh(pos, values, color=colors, height=0.7, edgecolor="none")
        ax.set_yticks(pos)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()            # biggest bar on top
        ax.margins(x=0.20)
    else:
        bars = ax.bar(pos, values, color=colors, width=0.7, edgecolor="none")
        ax.set_xticks(pos)
        ax.set_xticklabels(labels, rotation=rotate,
                           ha="right" if rotate else "center", rotation_mode="anchor")
        ax.margins(y=0.14)
    if horizontal or len(values) <= 12:
        ax.bar_label(bars, labels=[_label_value(v, money) for v in values],
                     padding=4, fontsize=9.5, fontweight="bold", color=C["text"])


# ---------------------------------------------------------------------------
# Three generic building blocks: bar / line / histogram
# ---------------------------------------------------------------------------

def bar_chart(df, group_col, value_col, title, agg="sum", rotate=45, top_n=None, horizontal=False):
    """Group `value_col` by `group_col` and plot as a bar chart.
    Used for: sales by city/state, top products, sales by day, etc.
    """
    data = df.groupby(group_col)[value_col].agg(agg).sort_values(ascending=False)
    if top_n:
        data = data.head(top_n)

    labels = [str(i) for i in data.index]
    values = list(data.values)
    money = value_col == "Sales"

    height = max(4.2, 0.34 * len(values)) if horizontal else 4.2
    fig, ax = plt.subplots(figsize=(7, height))
    _draw_bars(ax, labels, values, horizontal, rotate, money)

    if horizontal:
        return _finish(fig, ax, title, value_col, "", grid_axis="x",
                       money_axis="x" if money else None)
    return _finish(fig, ax, title, group_col, value_col, grid_axis="y",
                   money_axis="y" if money else None)


def line_chart(df, group_col, value_col, title, agg="sum", sort_order=None):
    """Group `value_col` by `group_col` and plot as a line chart.
    Used for: sales trend by month, orders by hour, etc.
    """
    data = df.groupby(group_col)[value_col].agg(agg)
    if sort_order:
        data = data.reindex(sort_order)
    else:
        data = data.sort_index()

    money = value_col == "Sales"
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(data.index, data.values, color=C["primary"], linewidth=2.8,
            marker="o", markersize=7, markerfacecolor=C["card"],
            markeredgecolor=C["primary"], markeredgewidth=2)
    ax.fill_between(data.index, data.values, color=C["primary"], alpha=0.14)

    # Print the peak value so the best point is readable at a glance
    peak_x, peak_y = data.idxmax(), data.max()
    ax.annotate(f"Peak {_label_value(peak_y, money)}", xy=(peak_x, peak_y),
                xytext=(0, 12), textcoords="offset points", ha="center",
                fontsize=9.5, fontweight="bold", color=C["text"])
    ax.margins(y=0.15)
    ax.set_ylim(bottom=0)   # no empty space below zero

    # Show Jan..Dec instead of 1..12, and whole hours instead of 6.5, 7.5...
    if group_col == "Month":
        ax.set_xticks(list(data.index))
        ax.set_xticklabels([MONTH_NAMES[int(m) - 1] for m in data.index])
    elif group_col == "Hour":
        ax.set_xticks(list(data.index))

    return _finish(fig, ax, title, group_col, value_col, grid_axis="y",
                   money_axis="y" if money else None)


def histogram(df, col, title):
    """Plot the distribution of a single numeric column.
    Used for: order quantity spread, price spread, etc.
    """
    fig, ax = plt.subplots(figsize=(7, 4.2))
    sns.histplot(df[col], kde=True, color=C["primary"], edgecolor=C["card"], alpha=0.9,
                 line_kws={"color": C["contrast"], "linewidth": 2.8}, ax=ax)
    return _finish(fig, ax, title, col, "Count", grid_axis="y",
                   money_axis="x" if col == "Price Each" else None)


# ---------------------------------------------------------------------------
# Sold-together analysis (its own thing — not a bar/line/histogram)
# ---------------------------------------------------------------------------

def analyze_sold_together(df, top_n=10):
    """Find which two products most often appear in the same order."""
    if "Order ID" not in df.columns or "Product" not in df.columns:
        return []

    dup = df[df["Order ID"].duplicated(keep=False)]
    grouped = dup.groupby("Order ID")["Product"].apply(lambda x: sorted(set(x)))

    counter = Counter()
    for products in grouped:
        if len(products) > 1:
            counter.update(combinations(products, 2))

    return counter.most_common(top_n)


def sold_together_chart(df, top_n=10):
    combos = analyze_sold_together(df, top_n)
    if not combos:
        return None
    labels = [f"{a} + {b}" for (a, b), _ in combos]
    counts = [c for _, c in combos]

    fig, ax = plt.subplots(figsize=(7, max(4.2, 0.5 * len(labels))))
    _draw_bars(ax, labels, counts, horizontal=True, rotate=0, money=False)
    return _finish(fig, ax, "Most Frequently Bought Together",
                   "Times bought together", "", grid_axis="x")


# ---------------------------------------------------------------------------
# Master chart list — this is the only place you need to touch to add,
# remove, or change a chart.
# ---------------------------------------------------------------------------

def create_visualizations(df):
    """Build every chart that this dataset has the columns for.

    Each entry below says: "if these columns exist, build this chart".
    To add a new chart, add one line here — no new function needed.
    """
    figs = {}

    chart_list = [
        ("Monthly Sales Trend", ["Month", "Sales"],
         lambda: line_chart(df, "Month", "Sales", "Monthly Sales Trend")),

        ("Sales by Day of Week", ["DayName", "Sales"],
         lambda: bar_chart(df, "DayName", "Sales", "Sales by Day of Week", rotate=0)),

        ("Best Hour for Ads", ["Hour", "Quantity Ordered"],
         lambda: line_chart(df, "Hour", "Quantity Ordered", "Best Hour for Ads")),

        ("Sales by City", ["City", "Sales"],
         lambda: bar_chart(df, "City", "Sales", "Sales by City")),

        ("Sales by State", ["State", "Sales"],
         lambda: bar_chart(df, "State", "Sales", "Sales by State", rotate=0)),

        # Products have long names -> horizontal bars so every name is readable
        ("Top Products by Revenue", ["Product", "Sales"],
         lambda: bar_chart(df, "Product", "Sales", "Top Products by Revenue", horizontal=True)),

        ("Most Sold Products (Quantity)", ["Product", "Quantity Ordered"],
         lambda: bar_chart(df, "Product", "Quantity Ordered", "Most Sold Products (Quantity)", horizontal=True)),

        ("Order Quantity Distribution", ["Quantity Ordered"],
         lambda: histogram(df, "Quantity Ordered", "Order Quantity Distribution")),

        ("Product Price Distribution", ["Price Each"],
         lambda: histogram(df, "Price Each", "Product Price Distribution")),

        ("Most Frequently Bought Together", ["Order ID", "Product"],
         lambda: sold_together_chart(df)),
    ]

    for title, required_cols, build_fn in chart_list:
        if all(col in df.columns for col in required_cols):
            try:
                fig = build_fn()
                if fig is not None:
                    figs[title] = fig
            except Exception:
                pass  # skip a chart that fails rather than crash the whole page

    return figs
