# pages/1_📊_Analysis.py
import streamlit as st
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import get_raw_data
import plotly.express as px

df = get_raw_data()
all_platforms = sorted(df['platform'].unique())

with st.sidebar:
    selected_platforms = st.multiselect(
        "Filter by Platform",
        options=all_platforms,
        default=all_platforms
    )

# Filter data
if selected_platforms:
    df_filtered = df[df['platform'].isin(selected_platforms)]
else:
    df_filtered = df

st.title(f"📊 Platform & Category Analysis ({len(selected_platforms)} platforms selected)")

# ── Chart 1: Average Budget by Platform (cached aggregation) ───────
@st.cache_data
def get_platform_avg_budget(df):
    return df.groupby("platform")["budget_inr"].mean().round(0).reset_index()

platform_avg = get_platform_avg_budget(df_filtered)
fig1 = px.bar(
    platform_avg,
    x="platform",
    y="budget_inr",
    title=f"Average Budget by Platform ({len(selected_platforms)} selected)",
    labels={"budget_inr": "Avg Budget (₹)", "platform": "Platform"},
    color="budget_inr",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Project Count by Category (horizontal, sorted) ────────
category_counts = df_filtered['category'].value_counts().reset_index()
category_counts.columns = ['Category', 'Count']
category_counts = category_counts.sort_values('Count', ascending=True)  # for horizontal bar

fig2 = px.bar(
    category_counts,
    x="Count",
    y="Category",
    orientation="h",
    title="Project Count by Category (sorted descending)",
    color="Count",
    color_continuous_scale="Greens"
)
fig2.update_layout(yaxis=dict(autorange="reversed"))  # highest at top
st.plotly_chart(fig2, use_container_width=True)