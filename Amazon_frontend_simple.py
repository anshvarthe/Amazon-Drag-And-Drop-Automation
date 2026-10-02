"""
Amazon Sales Dashboard — Frontend (Streamlit, restyled v2)
============================================================================
This file does 5 things, in order:
  1. Let the user upload a file
  2. Run it through the backend pipeline (load -> clean -> feature engineer)
  3. Show a few filters in the sidebar
  4. Show KPI numbers
  5. Loop over every chart the backend built and display it

Colors come from the COLOR CONFIG in Amazon_backend_simple.py (dict `C`).
Use the "Dark mode" switch and "Color theme" picker at the top of the sidebar.
"""

from html import escape

import streamlit as st
from Amazon_backend_simple import (
    C,
    THEME,
    ACCENT,
    ACCENTS,
    set_theme,
    load_single_file,
    clean_data,
    feature_engineering,
    add_city_state_column,
    get_kpis,
    analyze_sold_together,
    create_visualizations,
)

st.set_page_config(page_title="Amazon Sales Dashboard", page_icon="📊", layout="wide")

# ---------------------------------------------------------------------------
# THEME SWITCH — first thing in the sidebar, works before AND after upload
# ---------------------------------------------------------------------------

dark_mode = st.sidebar.toggle("🌙 Dark mode", value=(THEME == "dark"), key="dark_mode")
accent = st.sidebar.selectbox("🎨 Color theme", list(ACCENTS),
                              index=list(ACCENTS).index(ACCENT), key="accent")
set_theme("dark" if dark_mode else "light", accent)   # updates C in place -> charts + CSS follow

# ---------------------------------------------------------------------------
# STYLE — all colors are CSS variables in :root (generated from the palette)
# ---------------------------------------------------------------------------

_ROOT_VARS = f"""
:root {{
    color-scheme: {'dark' if dark_mode else 'light'};
    --bg: {C['bg']};
    --sidebar: {C['sidebar']};
    --card: {C['card']};
    --border: {C['border']};
    --text: {C['text']};
    --muted: {C['muted']};
    --primary: {C['primary']};
    --primary-hover: {C['primary_hover']};
    --primary-disabled: {C['primary_disabled']};
    --primary-soft: {C['primary_soft']};
    --on-primary: {C['on_primary']};
    --hero-from: {C['hero_from']};
    --hero-to: {C['hero_to']};
    --positive: {C['positive']};
    --negative: {C['negative']};
    --shadow: {C['shadow']};
    --shadow-hover: {C['shadow_hover']};
    --radius: 14px;
}}
"""

_CSS = """
/* ---------- page + text ---------- */
.stApp, [data-testid="stAppViewContainer"] { background: var(--bg); color: var(--text); }
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3, h4, h5, h6, p, label, li, .stMarkdown { color: var(--text); }
[data-testid="stSidebar"] { background: var(--sidebar); border-right: 1px solid var(--border); }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: var(--text); }
.block-container { padding-top: 2rem; max-width: 1280px; }

/* ---------- hero header ---------- */
.hero { background: linear-gradient(135deg, var(--hero-from), var(--hero-to));
        border-radius: var(--radius); padding: 28px 32px; margin-bottom: 24px;
        box-shadow: var(--shadow); }
.hero, .hero h1, .hero h1 *, .hero p, .hero p * { color: #FFFFFF !important; }
.hero h1 { margin: 0; font-size: 2rem; }
.hero p  { margin: 6px 0 0 0; opacity: 0.9; }

/* ---------- upload drag-and-drop zone ---------- */
[data-testid="stFileUploaderDropzone"] {
    background: var(--primary-soft); border: 2px dashed var(--primary);
    border-radius: var(--radius); padding: 28px; transition: all .2s ease; }
[data-testid="stFileUploaderDropzone"]:hover {
    background: var(--card); transform: translateY(-2px); box-shadow: var(--shadow-hover); }
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] span { color: var(--muted); }
[data-testid="stFileUploaderFile"] { background: var(--card); border-radius: 10px; }
[data-testid="stFileUploaderFileName"] { color: var(--text); }

/* ---------- buttons (text is forced to be visible) ---------- */
.stButton > button, [data-testid="stFileUploaderDropzone"] button,
[data-testid="stBaseButton-secondary"] {
    background: var(--primary); border: none; border-radius: 10px;
    padding: 8px 20px; font-weight: 700; transition: all .2s ease; }
.stButton > button, .stButton > button *,
[data-testid="stFileUploaderDropzone"] button, [data-testid="stFileUploaderDropzone"] button *,
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondary"] * {
    color: var(--on-primary) !important; }
.stButton > button:hover, [data-testid="stFileUploaderDropzone"] button:hover,
[data-testid="stBaseButton-secondary"]:hover {
    background: var(--primary-hover); transform: translateY(-1px); box-shadow: var(--shadow-hover); }
.stButton > button:disabled, [data-testid="stFileUploaderDropzone"] button:disabled {
    background: var(--primary-disabled); cursor: not-allowed; transform: none; box-shadow: none; }

/* ---------- KPI cards (custom HTML) ---------- */
.kpi { background: var(--card); border: 1px solid var(--border); border-left: 4px solid var(--primary);
       border-radius: var(--radius); padding: 16px 20px; min-height: 104px; margin-bottom: 16px;
       box-shadow: var(--shadow); transition: all .2s ease; }
.kpi:hover { transform: translateY(-3px); box-shadow: var(--shadow-hover); }
.kpi-label { color: var(--muted); font-size: 0.9rem; font-weight: 500; margin-bottom: 6px; }
.kpi-value { color: var(--text); font-size: 2rem; font-weight: 700; line-height: 1.15; }
.kpi-text .kpi-value { font-size: 1.15rem; line-height: 1.35; padding-top: 6px;
                       white-space: normal; word-break: break-word; }

/* ---------- chart cards (st.container(border=True)) ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card); border: 1px solid var(--border) !important;
    border-radius: var(--radius); box-shadow: var(--shadow); transition: all .2s ease; }
[data-testid="stVerticalBlockBorderWrapper"]:hover { transform: translateY(-3px); box-shadow: var(--shadow-hover); }

/* ---------- inputs, tags, dropdowns ---------- */
[data-baseweb="select"] > div { background: var(--card); border-color: var(--border); border-radius: 10px; }
[data-baseweb="select"] input, [data-baseweb="select"] div { color: var(--text); }
span[data-baseweb="tag"] { background: var(--primary) !important; border-radius: 8px; }
span[data-baseweb="tag"], span[data-baseweb="tag"] * { color: var(--on-primary) !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] li { background: var(--card); color: var(--text); }
[data-baseweb="popover"] li:hover { background: var(--primary-soft); }

/* ---------- alerts (info / green success / red error) ---------- */
[data-testid="stAlert"] { background: var(--primary-soft); border: 1px solid var(--border);
                          border-radius: var(--radius); box-shadow: var(--shadow); }
[data-testid="stAlert"] * { color: var(--text); }
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) { border-left: 5px solid var(--positive); }
[data-testid="stAlert"]:has([data-testid="stAlertContentError"])   { border-left: 5px solid var(--negative); }

/* ---------- spinner + data table ---------- */
[data-testid="stSpinner"] * { color: var(--primary) !important; }
.dwrap { overflow-x: auto; background: var(--card); border: 1px solid var(--border);
         border-radius: var(--radius); box-shadow: var(--shadow); }
.dtable { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.dtable th { background: var(--primary-soft); color: var(--text); text-align: left !important;
             padding: 10px 12px; white-space: nowrap; }
.dtable td { color: var(--text); padding: 8px 12px; border-top: 1px solid var(--border); white-space: nowrap; }
.dtable tr:hover td { background: var(--primary-soft); }
"""

st.markdown(f"<style>{_ROOT_VARS}{_CSS}</style>", unsafe_allow_html=True)


def kpi_card(label, value, small=False):
    """One KPI card. small=True uses a smaller, wrapping font for long text values."""
    cls = "kpi kpi-text" if small else "kpi"
    return (f'<div class="{cls}"><div class="kpi-label">{escape(label)}</div>'
            f'<div class="kpi-value">{escape(str(value))}</div></div>')


st.markdown(
    '<div class="hero"><h1>📊 Amazon Sales Dashboard</h1>'
    '<p>Upload your sales file to see key metrics and charts in seconds.</p></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 1 & 2. Upload and process the file
# ---------------------------------------------------------------------------

uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if not uploaded_file:
    st.info("⬆ Please upload a CSV or Excel file to begin.")
    st.stop()

try:
    with st.spinner("Processing your data..."):
        df = load_single_file(uploaded_file)
        df = clean_data(df)
        df = feature_engineering(df)
        if "Purchase Address" in df.columns:
            df = add_city_state_column(df)
except Exception as e:
    st.error(f"Could not process this file: {e}")
    st.stop()

st.success(f"✅ Loaded **{uploaded_file.name}** — {len(df):,} rows ready.")

# ---------------------------------------------------------------------------
# 3. Sidebar filters (optional — just narrows down `df` before we use it)
# ---------------------------------------------------------------------------

st.sidebar.header("Filters")

if "City" in df.columns:
    cities = sorted(df["City"].dropna().unique())
    chosen_cities = st.sidebar.multiselect("City", cities)
    if chosen_cities:
        df = df[df["City"].isin(chosen_cities)]

if "Product" in df.columns:
    products = sorted(df["Product"].dropna().unique())
    chosen_products = st.sidebar.multiselect("Product", products)
    if chosen_products:
        df = df[df["Product"].isin(chosen_products)]

# ---------------------------------------------------------------------------
# 4. KPI numbers (3 per row; text values use a smaller font so names fit)
# ---------------------------------------------------------------------------

st.subheader("📌 Key Metrics")
kpis = get_kpis(df)

row1 = st.columns(3)
row1[0].markdown(kpi_card("Total Sales", f"${kpis['total_sales']:,.2f}"), unsafe_allow_html=True)
row1[1].markdown(kpi_card("Total Orders", f"{kpis['total_orders']:,}"), unsafe_allow_html=True)
row1[2].markdown(kpi_card("Unique Products", f"{kpis['unique_products']:,}"), unsafe_allow_html=True)

row2 = st.columns(3)
row2[0].markdown(kpi_card("Avg Order Value", f"${kpis['avg_order_value']:,.2f}"), unsafe_allow_html=True)
row2[1].markdown(kpi_card("Top Product", kpis["top_product"], small=True), unsafe_allow_html=True)
row2[2].markdown(kpi_card("Top City", kpis["top_city"], small=True), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 5. Charts — just loop over whatever the backend gives us, two per row
# ---------------------------------------------------------------------------

st.subheader("📈 Charts")
charts = create_visualizations(df)
titles = list(charts.keys())

for i in range(0, len(titles), 2):
    col1, col2 = st.columns(2)
    for col, title in zip([col1, col2], titles[i:i + 2]):
        with col:
            with st.container(border=True):
                st.pyplot(charts[title], use_container_width=True)

# ---------------------------------------------------------------------------
# Sold-together list (text version, alongside the chart above)
# ---------------------------------------------------------------------------

st.subheader("🤝 Most Often Sold Together")
combos = analyze_sold_together(df)
if combos:
    for (product_a, product_b), count in combos:
        st.write(f"- **{product_a} + {product_b}** → bought together **{count}** times")
else:
    st.info("No product combination data available.")

# ---------------------------------------------------------------------------
# Raw data preview (HTML table so it follows the light/dark theme)
# ---------------------------------------------------------------------------

st.subheader("📝 Data Preview")
st.markdown(
    '<div class="dwrap">' + df.head(20).to_html(index=False, border=0, classes="dtable") + "</div>",
    unsafe_allow_html=True,
)
