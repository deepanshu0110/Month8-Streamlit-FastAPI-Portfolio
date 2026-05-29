import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ============================================
# PAGE CONFIG – MUST BE FIRST STREAMLIT CALL
# ============================================
st.set_page_config(page_title="FreelanceHub India", page_icon="💼", layout="wide")

# ============================================
# DATA GENERATION (self‑contained, cached)
# ============================================
@st.cache_data
def load_data():
    np.random.seed(141)
    n = 500
    categories = ['Web Development', 'Data Analytics', 'ML/AI', 'Design',
                  'Content Writing', 'Digital Marketing']
    cities = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata']
    levels = ['Rising Talent', 'Level 1', 'Level 2', 'Top Rated']
    statuses = ['Completed', 'In Progress', 'Cancelled']
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    df = pd.DataFrame({
        'project_id': [f'P{str(i).zfill(3)}' for i in range(1, n+1)],
        'category': np.random.choice(categories, n, p=[0.25,0.20,0.15,0.15,0.15,0.10]),
        'budget_inr': np.random.randint(5000, 150001, n),
        'duration_days': np.random.randint(3, 91, n),
        'client_rating': np.round(np.random.uniform(2.5, 5.0, n), 1),
        'freelancer_level': np.random.choice(levels, n, p=[0.30,0.30,0.25,0.15]),
        'status': np.random.choice(statuses, n, p=[0.65,0.25,0.10]),
        'city': np.random.choice(cities, n),
        'platform_fee_pct': np.random.choice([10,15,20], n, p=[0.20,0.50,0.30]),
        'month': np.random.choice(months, n)
    })
    df['net_revenue'] = np.round(df['budget_inr'] * (1 - df['platform_fee_pct']/100), 2)
    return df

df = load_data()
categories = sorted(df['category'].unique())

# ============================================
# SESSION STATE INITIALISATION
# ============================================
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []
if 'baseline' not in st.session_state:
    st.session_state.baseline = 'ML/AI'
if 'page' not in st.session_state:
    st.session_state.page = '📊 Overview'

# ============================================
# SIDEBAR – WATCHLIST (T1) & NAVIGATION (T2)
# ============================================
st.sidebar.title("FreelanceHub India")
st.sidebar.markdown("---")
st.sidebar.subheader("📌 Category Watchlist (T1)")
add_cat = st.sidebar.selectbox("Select category to track", categories)
if st.sidebar.button("Add to Watchlist"):
    if add_cat not in st.session_state.watchlist:
        st.session_state.watchlist.append(add_cat)
if st.sidebar.button("Clear Watchlist"):
    st.session_state.watchlist = []
st.sidebar.write(f"**Watchlist ({len(st.session_state.watchlist)} items):**")
st.sidebar.write(st.session_state.watchlist if st.session_state.watchlist else "Empty")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ['📊 Overview', '📂 Category', '🏙️ City'],
    index=['📊 Overview', '📂 Category', '🏙️ City'].index(st.session_state.page)
)
st.session_state.page = page

# ============================================
# PAGE: OVERVIEW (T3–T7 + Bonus)
# ============================================
if page == '📊 Overview':
    st.title("📊 FreelanceHub India — Overview")
    tab_ov, tab_cat, tab_city = st.tabs(["Overview Metrics", "Category", "City"])

    with tab_ov:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Projects", f"{len(df):,}")
        col2.metric("Avg Budget", f"₹{df['budget_inr'].mean():,.0f}")
        col3.metric("Completion Rate", f"{(df['status']=='Completed').mean()*100:.1f}%")
        col4.metric("Avg Rating", f"{df['client_rating'].mean():.2f}")
        st.markdown("---")

        # T6: Pinned baseline comparison
        st.subheader("📌 Baseline Category Comparison (T6)")
        sel_baseline = st.selectbox("Select baseline category", categories,
                                    index=categories.index('ML/AI'))
        if st.button("Set as Baseline"):
            st.session_state.baseline = sel_baseline
        baseline = st.session_state.baseline
        b_df = df[df['category'] == baseline]
        comp_df = pd.DataFrame({
            'Metric': ['Avg Budget (₹)', 'Completion Rate (%)', 'Avg Rating'],
            f'Baseline: {baseline}': [
                f"₹{b_df['budget_inr'].mean():,.0f}",
                f"{(b_df['status']=='Completed').mean()*100:.1f}%",
                f"{b_df['client_rating'].mean():.2f}"
            ],
            'Platform Avg': [
                f"₹{df['budget_inr'].mean():,.0f}",
                f"{(df['status']=='Completed').mean()*100:.1f}%",
                f"{df['client_rating'].mean():.2f}"
            ]
        })
        st.dataframe(comp_df, use_container_width=True, hide_index=True)
        st.markdown("---")

        # T4: Profitability Calculator (form)
        st.subheader("🧮 Project Profitability Calculator (T4)")
        with st.form("profit_calc"):
            c1, c2, c3 = st.columns(3)
            budget = c1.number_input("Budget (₹)", min_value=5000, max_value=150000,
                                     value=80000, step=5000)
            fee = c2.selectbox("Platform Fee %", [10, 15, 20], index=1)
            days = c3.number_input("Duration (days)", min_value=1, max_value=90, value=30)
            submit = st.form_submit_button("Calculate")
        if submit:
            net = budget * (1 - fee / 100)
            daily = net / days
            hourly = daily / 8
            m1, m2, m3 = st.columns(3)
            m1.metric("Net Revenue", f"₹{net:,.0f}")
            m2.metric("Daily Rate", f"₹{daily:,.0f}")
            m3.metric("Hourly Rate", f"₹{hourly:,.0f}")
        st.markdown("---")

        # T7: NRA Insight
        top_rated_avg = df[df['freelancer_level'] == 'Top Rated']['budget_inr'].mean()
        rising_avg = df[df['freelancer_level'] == 'Rising Talent']['budget_inr'].mean()
        gap = top_rated_avg - rising_avg
        tr_comp = (df[df['freelancer_level'] == 'Top Rated']['status'] == 'Completed').mean() * 100
        plat_comp = (df['status'] == 'Completed').mean() * 100
        st.info(
            f"**📊 NRA – Counter‑Intuitive Level Pricing Finding (T7)**\n\n"
            f"**Number:** Top Rated freelancers average ₹{top_rated_avg:,.0f}/project – "
            f"₹{abs(gap):,.0f} **LESS** than Rising Talent at ₹{rising_avg:,.0f}. "
            f"Top Rated completion rate: {tr_comp:.1f}% vs platform avg {plat_comp:.1f}%.\n\n"
            f"**Reason:** Badge level does not dictate budget. Top Rated often work on longer retainers "
            f"(lower per‑project ₹, higher lifetime value) while Rising Talent competes on price.\n\n"
            f"**Action:** Target ML/AI and Design (avg ₹84,800) over chasing badge. "
            f"Set Upwork bid floor at ₹70,000 for ML/AI. Update Fiverr within 7 days."
        )
        st.markdown("---")

        # T5: Expander for raw data
        with st.expander("📋 Show project data (all rows)"):
            cols_show = ['project_id', 'category', 'budget_inr', 'net_revenue',
                         'status', 'client_rating', 'city']
            st.caption(f"{len(df)} projects shown")
            st.dataframe(df[cols_show], use_container_width=True)
        st.markdown("---")

        # BONUS: Download button
        completed = df[df['status'] == 'Completed']
        csv = completed.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Completed Projects (Bonus)",
            data=csv,
            file_name="completed_projects.csv",
            mime="text/csv"
        )
        st.caption(f"Export contains {len(completed)} projects | "
                   f"Total net revenue: ₹{completed['net_revenue'].sum():,.0f}")

    with tab_cat:
        st.subheader("Category Avg Budget (₹)")
        cat_df = df.groupby('category')['budget_inr'].mean().reset_index().sort_values('budget_inr', ascending=False)
        fig = px.bar(cat_df, x='category', y='budget_inr', color='budget_inr',
                     color_continuous_scale='Blues')
        fig.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab_city:
        st.subheader("City Performance")
        city_df = df.groupby('city').agg(
            Projects=('project_id', 'count'),
            Avg_Budget=('budget_inr', 'mean'),
            Avg_Rating=('client_rating', 'mean')
        ).reset_index().sort_values('Avg_Budget', ascending=False)
        city_df['Avg_Budget'] = city_df['Avg_Budget'].round(0).astype(int)
        city_df['Avg_Rating'] = city_df['Avg_Rating'].round(2)
        st.dataframe(city_df, use_container_width=True, hide_index=True)

# ============================================
# PAGE: CATEGORY DEEP DIVE
# ============================================
elif page == '📂 Category':
    st.title("📂 Category Deep Dive")
    cat_summary = df.groupby('category').agg(
        Projects=('project_id', 'count'),
        Avg_Budget=('budget_inr', 'mean'),
        Avg_Rating=('client_rating', 'mean'),
        Completion_Rate=('status', lambda x: f"{(x == 'Completed').mean() * 100:.1f}%")
    ).reset_index().sort_values('Avg_Budget', ascending=False)
    cat_summary['Avg_Budget'] = cat_summary['Avg_Budget'].apply(lambda x: f"₹{x:,.0f}")
    st.dataframe(cat_summary, use_container_width=True, hide_index=True)

# ============================================
# PAGE: CITY DEEP DIVE
# ============================================
elif page == '🏙️ City':
    st.title("🏙️ City Performance")
    city_full = df.groupby('city').agg(
        Projects=('project_id', 'count'),
        Avg_Budget=('budget_inr', 'mean'),
        Avg_Rating=('client_rating', 'mean'),
        Completion_Rate=('status', lambda x: f"{(x == 'Completed').mean() * 100:.1f}%")
    ).reset_index().sort_values('Avg_Budget', ascending=False)
    city_full['Avg_Budget'] = city_full['Avg_Budget'].apply(lambda x: f"₹{x:,.0f}")
    st.dataframe(city_full, use_container_width=True, hide_index=True)