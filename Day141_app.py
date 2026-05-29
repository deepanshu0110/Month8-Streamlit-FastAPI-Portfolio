import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="FreelanceHub India", page_icon="💼", layout="wide")
st.title("FreelanceHub India — Analytics Dashboard")
st.caption("Month 8 | Day 141 | Deepanshu Garg")

@st.cache_data
def load_data():
    return pd.read_csv("freelancehub_india.csv")

df = load_data()

st.sidebar.header("Filters")
selected_category = st.sidebar.selectbox(
    "Category",
    options=["All"] + sorted(df["category"].unique().tolist())
)

selected_cities = st.sidebar.multiselect(
    "City",
    options=sorted(df["city"].unique().tolist()),
    default=sorted(df["city"].unique().tolist())
)

budget_range = st.sidebar.slider(
    "Budget Range (INR)",
    min_value=int(df["budget_inr"].min()),
    max_value=int(df["budget_inr"].max()),
    value=(int(df["budget_inr"].min()), int(df["budget_inr"].max()))
)

filtered = df.copy()
if selected_category != "All":
    filtered = filtered[filtered["category"] == selected_category]
if selected_cities:
    filtered = filtered[filtered["city"].isin(selected_cities)]
filtered = filtered[
    (filtered["budget_inr"] >= budget_range[0]) &
    (filtered["budget_inr"] <= budget_range[1])
]

st.write(f"Showing **{len(filtered)}** projects")
st.divider()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Projects", len(filtered))
col2.metric("Avg Budget", f"Rs {filtered['budget_inr'].mean():,.0f}")
col3.metric("Avg Rating", f"{filtered['client_rating'].mean():.2f}")
col4.metric("Completion Rate", f"{(filtered['status'] == 'Completed').mean() * 100:.1f}%")
st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Projects by Category")
    cat_counts = filtered["category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    fig_bar = px.bar(cat_counts, x="Category", y="Count", color="Count",
                     color_continuous_scale="Blues", title="Project Count by Category")
    fig_bar.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with right:
    st.subheader("Avg Budget by Category")
    avg_budget = filtered.groupby("category")["budget_inr"].mean().reset_index()
    avg_budget.columns = ["Category", "Avg Budget (INR)"]
    avg_budget = avg_budget.sort_values("Avg Budget (INR)", ascending=True)
    fig_h = px.bar(avg_budget, x="Avg Budget (INR)", y="Category", orientation="h",
                   color="Avg Budget (INR)", color_continuous_scale="Greens",
                   title="Average Budget (INR) by Category")
    fig_h.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_h, use_container_width=True)

st.divider()

top_cat = filtered.groupby("category")["budget_inr"].mean().idxmax()
top_budget = filtered.groupby("category")["budget_inr"].mean().max()

st.info(
    f"**NRA INSIGHT** | "
    f"**Number:** {top_cat} projects average Rs {top_budget:,.0f} – "
    f"Rs {top_budget - filtered['budget_inr'].mean():,.0f} above platform average. "
    f"**Reason:** Higher technical complexity and smaller qualified freelancer supply "
    f"allow {top_cat} specialists to command premium rates. "
    f"**Action:** Prioritise {top_cat} bids on **Upwork**; set minimum proposal at "
    f"Rs {top_budget * 0.80:,.0f} to stay competitive while protecting margin. "
    f"Update **Fiverr** profile to list {top_cat} as primary skill within 7 days."
)

with st.expander("View Raw Filtered Data"):
    st.dataframe(filtered, use_container_width=True, height=300)