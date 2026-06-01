# app.py
import streamlit as st
import time
import sys
import os

# Add parent directory to path so we can import utils
sys.path.insert(0, os.path.dirname(__file__))
from utils.data_loader import get_raw_data, get_summary_stats

st.set_page_config(page_title="FreelanceHub India Dashboard", page_icon="💼", layout="wide")

# ── Sidebar refresh control ─────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Controls")
    if st.button("🔄 Refresh Data"):
        get_raw_data.clear()
        st.rerun()

# ── Load data with timing (first load vs cached) ───────────────────
t0 = time.time()
df = get_raw_data()
load_time = time.time() - t0

st.title("💼 FreelanceHub India Dashboard")
st.caption(f"Data loaded in {load_time:.4f}s  |  {len(df):,} projects  |  seed=141")

# ── 5 KPIs ─────────────────────────────────────────────────────────
stats = get_summary_stats(df)
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Projects",    f"{stats['total_projects']:,}")
col2.metric("Completion Rate",   f"{stats['completed_pct']}%")
col3.metric("Avg Budget",        f"₹{stats['avg_budget']:,.0f}")
col4.metric("Top Platform",      stats['top_platform'])
col5.metric("Null Values",       stats['null_count'])

st.info("👈 Use the sidebar to navigate to **Analysis** or **Prediction** pages.")