# day143_app.py
# Universal CSV Analyser with File Upload, Auto EDA, Dynamic Filters, and Download

import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# ------------------------------------------------------------------------------
# Page configuration (T1)
st.set_page_config(page_title="CSV Analyser", layout="wide")
st.title("📂 Universal CSV Analyser")
st.caption("Upload any CSV for instant EDA – dynamic insights, filtering, and download")

# ------------------------------------------------------------------------------
# Sidebar: file uploader (T1)
with st.sidebar:
    st.subheader("Upload Settings")
    uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])

    # Null state: stop execution if no file (T1)
    if uploaded_file is None:
        st.info("📂 Upload a CSV file in the sidebar to begin.")
        st.stop()  # halts app execution here

    st.success(f"✅ Loaded: {uploaded_file.name}")

# ------------------------------------------------------------------------------
# Load and cache data (T2)
@st.cache_data
def load_data(file_bytes: bytes) -> pd.DataFrame:
    """Read CSV from bytes and return DataFrame."""
    df = pd.read_csv(io.BytesIO(file_bytes))
    # If net_earnings is missing, compute it from budget_inr and platform_fee_pct
    if "net_earnings" not in df.columns and "budget_inr" in df.columns and "platform_fee_pct" in df.columns:
        df["net_earnings"] = df["budget_inr"] * (1 - df["platform_fee_pct"] / 100)
    return df

df = load_data(uploaded_file.read())

# ------------------------------------------------------------------------------
# Basic info metrics (T2)
rows, cols = df.shape
total_cells = rows * cols
col1, col2, col3 = st.columns(3)
col1.metric("📊 Rows", f"{rows:,}")
col2.metric("📋 Columns", f"{cols:,}")
col3.metric("🔢 Total Cells", f"{total_cells:,}")

# Data preview
st.subheader("📋 Data Preview (first 5 rows)")
st.dataframe(df.head(5), use_container_width=True)

# ------------------------------------------------------------------------------
# Auto EDA Section (T3)
st.subheader("🔍 Automatic EDA")

# Column types
col_types = df.dtypes.reset_index()
col_types.columns = ["Column", "Type"]
# Null analysis
null_counts = df.isnull().sum()
null_pct = (null_counts / rows) * 100
null_df = pd.DataFrame({
    "Column": null_counts.index,
    "Null Count": null_counts.values,
    "Null %": null_pct.round(1).values
})

left, right = st.columns(2)
with left:
    st.markdown("**📊 Column Types**")
    st.dataframe(col_types, use_container_width=True)
with right:
    st.markdown("**🚨 Null Analysis**")
    st.dataframe(null_df, use_container_width=True)

# Descriptive statistics
st.markdown("**📈 Descriptive Statistics**")
st.dataframe(df.describe().T.round(2), use_container_width=True)

# Numeric vs categorical counts
num_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = df.select_dtypes(include="object").columns.tolist()
col_metrics = st.columns(2)
col_metrics[0].metric("🔢 Numeric Columns", len(num_cols))
col_metrics[1].metric("🏷️ Categorical Columns", len(cat_cols))

# ------------------------------------------------------------------------------
# Dynamic Filter in sidebar (T4)
with st.sidebar:
    st.subheader("🎯 Filter Data")
    if len(cat_cols) > 0:
        selected_cat_col = st.selectbox("Filter by column:", options=cat_cols)
        unique_vals = sorted(df[selected_cat_col].unique())
        selected_vals = st.multiselect(
            "Select values:",
            options=unique_vals,
            default=unique_vals
        )
        # Apply filter
        df_filtered = df[df[selected_cat_col].isin(selected_vals)].copy()
    else:
        df_filtered = df.copy()
        selected_cat_col = None
        st.info("No categorical columns found – filter disabled.")

# Filter metrics (T4)
filtered_rows = len(df_filtered)
delta_rows = filtered_rows - rows
st.subheader("🎯 Filtered Data Overview")
filter_metrics = st.columns(2)
filter_metrics[0].metric(
    "Filtered Rows",
    f"{filtered_rows:,}",
    delta=f"{delta_rows:+d} rows"
)

# Average budget (if budget_inr exists, otherwise show message)
if "budget_inr" in df_filtered.columns:
    avg_budget = df_filtered["budget_inr"].mean()
    filter_metrics[1].metric("Avg Budget (₹)", f"₹{avg_budget:,.0f}")
else:
    filter_metrics[1].metric("Avg Budget (₹)", "N/A (no budget_inr column)")

# ------------------------------------------------------------------------------
# Distribution chart (T5)
st.subheader("📊 Distribution Analysis")
if len(num_cols) > 0:
    selected_num = st.selectbox("Select numeric column:", options=num_cols)
    fig_hist = px.histogram(
        df_filtered,
        x=selected_num,
        nbins=20,
        title=f"Distribution of {selected_num}",
        color_discrete_sequence=["#1F3864"]
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    mean_val = df_filtered[selected_num].mean()
    median_val = df_filtered[selected_num].median()
    std_val = df_filtered[selected_num].std()
    st.caption(
        f"Mean: ₹{mean_val:,.0f} | Median: ₹{median_val:,.0f} | Std: ₹{std_val:,.0f}"
    )
else:
    st.info("No numeric columns available for distribution chart.")

# ------------------------------------------------------------------------------
# Processed data preview + download (T6)
st.subheader("⬇️ Processed Data Preview (with budget_tier)")

# Add budget_tier column (bins: 0-25k, 25k-75k, >75k)
if "budget_inr" in df_filtered.columns:
    bins = [0, 25000, 75000, 150001]
    labels = ["Low (<25k)", "Mid (25-75k)", "High (>75k)"]
    df_filtered["budget_tier"] = pd.cut(
        df_filtered["budget_inr"],
        bins=bins,
        labels=labels,
        right=False
    )
else:
    df_filtered["budget_tier"] = "N/A (no budget_inr)"

# Show preview columns (including net_earnings if available)
preview_cols = ["project_id", "category", "budget_inr", "net_earnings", "budget_tier"]
available_preview = [c for c in preview_cols if c in df_filtered.columns]
if "net_earnings" not in available_preview:
    available_preview = [c for c in preview_cols if c != "net_earnings"]
st.dataframe(df_filtered[available_preview].head(10), use_container_width=True)

# Download button
csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Processed CSV",
    data=csv_bytes,
    file_name="processed_freelancehub.csv",
    mime="text/csv"
)
st.caption(f"Downloading {len(df_filtered)} rows × {len(df_filtered.columns)} columns")

# ------------------------------------------------------------------------------
# NRA Insight (T7) – now net_earnings is guaranteed to exist (computed if missing)
st.subheader("📌 NRA Insight: Freelancer Earnings by Level")

if "freelancer_level" in df_filtered.columns and "net_earnings" in df_filtered.columns:
    earnings_by_level = df_filtered.groupby("freelancer_level")["net_earnings"].mean().sort_values()
    highest_level = earnings_by_level.idxmax()
    highest_avg = earnings_by_level.max()
    lowest_level = earnings_by_level.idxmin()
    lowest_avg = earnings_by_level.min()
    gap = highest_avg - lowest_avg
    gap_pct = (gap / lowest_avg) * 100

    st.success(
    f"**Number:** {highest_level} freelancers earn the highest average net earnings (₹{highest_avg:,.0f}), "
    f"while {lowest_level} earn the lowest (₹{lowest_avg:,.0f}). The gap is ₹{gap:,.0f} ({gap_pct:.1f}%).\n\n"
    f"**Reason:** Even though Top Rated freelancers often command higher budgets, they are charged higher platform fees "
    f"(20% vs. 10–15% for Level 1). The combination of fee structure and project mix reduces their net take‑home.\n\n"
    f"**Action:** If you are Top Rated, target projects on platforms with a 10–15% fee (or negotiate a fee cap). "
    f"Alternatively, if you are Level 2, aim for Top Rated status but avoid 20%‑fee projects. Set a minimum budget "
    f"of ₹80,000 to compensate for higher fees. Review your last 10 projects and renegotiate fees within 30 days."
)
else:
    st.info("Required columns ('freelancer_level' and 'net_earnings') missing for NRA insight.")

# ------------------------------------------------------------------------------
# ★ Bonus: Correlation Heatmap (10★)
if len(num_cols) >= 2:
    st.subheader("🔗 Correlation Heatmap (Numeric Columns)")
    corr_matrix = df_filtered[num_cols].corr().round(3)
    fig_corr = px.imshow(
        corr_matrix,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Pearson Correlation — Numeric Features"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    # Strongest non-self correlation
    # Create mask to exclude diagonal (self-correlation = 1)
    mask = np.ones_like(corr_matrix, dtype=bool)
    np.fill_diagonal(mask, False)
    max_corr = corr_matrix.where(mask).max().max()
    # Find pair with that correlation
    for i in range(len(corr_matrix.columns)):
        for j in range(len(corr_matrix.columns)):
            if i != j and abs(corr_matrix.iloc[i, j] - max_corr) < 0.001:
                pair = (corr_matrix.columns[i], corr_matrix.columns[j])
                break
    st.caption(
        f"**Strongest non‑self correlation:** {pair[0]} ↔ {pair[1]} = {max_corr:.3f} "
        f"(expected ~0.997 between budget_inr and net_earnings)."
    )
else:
    st.info("At least two numeric columns required for correlation heatmap.")