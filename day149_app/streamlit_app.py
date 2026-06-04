import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ---------- Config ----------
BASE_URL = "http://localhost:8000"
API_KEY  = "freelancehub-2024-secret"
HEADERS  = {"X-API-Key": API_KEY}

# ---------- Safe API Call ----------
def safe_api_call(url, params=None, method="get", payload=None):
    try:
        if method == "get":
            r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        else:
            r = requests.post(url, headers=HEADERS, json=payload, timeout=10)

        if r.status_code == 200:
            return r.json(), None
        elif r.status_code == 401:
            return None, "❌ Unauthorized – check API key."
        elif r.status_code == 422:
            detail = r.json().get("detail", r.text)
            return None, f"❌ Validation error: {detail}"
        else:
            return None, f"❌ API error {r.status_code}: {r.text}"
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot reach API. Is FastAPI running on port 8000?"
    except requests.exceptions.Timeout:
        return None, "❌ Request timed out."
    except Exception as e:
        return None, f"❌ Unexpected error: {e}"

# ---------- Page config ----------
st.set_page_config(page_title="FreelanceHub Dashboard", layout="wide", page_icon="📊")
st.title("📊 FreelanceHub India — Live Dashboard")
st.caption("Data served by FastAPI · Streamlit frontend · 500 projects")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ API Settings")
    health_data, health_err = safe_api_call(f"{BASE_URL}/")
    if health_err:
        st.error("🔴 API Offline")
        st.code("uvicorn day149_api.main:app --reload --port 8000", language="bash")
    else:
        st.success("🟢 API Online")
        st.json(health_data)
    st.divider()
    st.markdown(f"[📚 API Docs (Swagger)]({BASE_URL}/docs)")
    st.markdown(f"[📄 ReDoc]({BASE_URL}/redoc)")
    st.divider()
    st.write("**API Key:**")
    st.code(API_KEY[:20] + "...", language="text")
    if st.button("🔄 Clear Cache"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.caption("FreelanceHub India · seed=141\nFastAPI:8000 · Streamlit:8501")

# ---------- 1. KPI Dashboard (cached) ----------
@st.cache_data(ttl=60)
def get_stats():
    return safe_api_call(f"{BASE_URL}/projects/stats")

stats_data, stats_err = get_stats()
if stats_err:
    st.error(stats_err)
    st.info("💡 Start FastAPI first:  uvicorn day149_api.main:app --reload --port 8000")
    st.stop()

# Safe division for completion rate
total = stats_data.get("total_projects", 0)
completed = stats_data.get("completed", 0)
completion_rate = (completed / total * 100) if total > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Projects", total)
with col2:
    st.metric("Completed", completed, delta=f"{completion_rate:.1f}% rate")
with col3:
    st.metric("Avg Hourly Rate", f"${stats_data.get('avg_hourly_rate', 0)}")
with col4:
    st.metric("High-Value (>$5k)", stats_data.get("high_value_count", 0))

# ---------- Platform Summary Chart ----------
@st.cache_data(ttl=60)
def get_platform_summary():
    return safe_api_call(f"{BASE_URL}/projects/platform-summary")

pdata, perr = get_platform_summary()
if not perr and pdata:
    pf_df = pd.DataFrame(pdata)
    st.subheader("📈 Platform Performance")
    col_a, col_b = st.columns(2)
    with col_a:
        fig1 = px.bar(pf_df, x="platform", y="count", text="count",
                      title=f"Projects by Platform — {pf_df.iloc[0]['platform']} leads with {pf_df.iloc[0]['count']} projects",
                      color="platform", color_discrete_sequence=px.colors.qualitative.Set2)
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    with col_b:
        fig2 = px.bar(pf_df, x="platform", y="avg_project_value", text="avg_project_value",
                      title=f"Avg Project Value — {pf_df.sort_values('avg_project_value',ascending=False).iloc[0]['platform']} leads at ${pf_df.sort_values('avg_project_value',ascending=False).iloc[0]['avg_project_value']:,.2f}",
                      color="platform", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_traces(texttemplate='$%{text:,.0f}')
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning(f"Platform summary unavailable: {perr or 'No data'}")

# ---------- Tabs ----------
tab1, tab2 = st.tabs(["🔍 Filter Projects", "🤖 Predict High-Value"])

# Tab 1: Filter by status
with tab1:
    st.subheader("🔍 Filter Projects by Status")
    status_choice = st.selectbox("Select project status", ["Completed", "In Progress", "Cancelled"])
    if st.button("🔎 Fetch Projects", key="filter_btn"):
        fdata, ferr = safe_api_call(f"{BASE_URL}/projects/filter", params={"status": status_choice})
        if ferr:
            st.error(ferr)
        else:
            st.success(f"✅ Found {len(fdata)} projects with status: **{status_choice}**")
            df_filter = pd.DataFrame(fdata)
            col_x, col_y, col_z = st.columns(3)
            with col_x:
                st.metric("Count", len(df_filter))
            with col_y:
                st.metric("Avg Hourly Rate", f"${df_filter['hourly_rate'].mean():.2f}" if len(df_filter) else "$0")
            with col_z:
                st.metric("Avg Project Value", f"${df_filter['project_value'].mean():,.2f}" if len(df_filter) else "$0")
            st.dataframe(df_filter[['project_id','platform','skill','experience',
                                    'hourly_rate','project_value','client_rating']],
                         use_container_width=True, hide_index=True)
            if len(df_filter):
                top_skill = df_filter.groupby('skill')['project_value'].mean().idxmax()
                top_val   = df_filter.groupby('skill')['project_value'].mean().max()
                st.info(f"💡 **NRA Insight:** Among {status_choice} projects, **{top_skill}** generates the highest avg project value at **${top_val:,.2f}**. Action: prioritise {top_skill} proposals to maximise {status_choice} earnings.")

# Tab 2: Predict high-value
with tab2:
    st.subheader("🤖 Predict: High-Value Project?")
    st.caption("Project value > $5,000 = High‑Value")
    with st.form("predict_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            p_platform = st.selectbox("Platform", ["Upwork","Freelancer","Fiverr","Toptal"])
            p_skill    = st.selectbox("Skill", ["Python","SQL","ML","Tableau","Excel","NLP"])
        with c2:
            p_exp      = st.selectbox("Experience", ["Junior","Mid","Senior","Expert"])
            p_type     = st.selectbox("Project Type", ["Fixed","Hourly"])
        with c3:
            p_hours    = st.slider("Hours Billed", 5, 200, 80)
            p_rate     = st.slider("Hourly Rate ($)", 10.0, 100.0, 55.0, 0.5)
            p_rating   = st.slider("Client Rating", 2.5, 5.0, 4.2, 0.1)
        submitted = st.form_submit_button("🚀 Predict")

    if submitted:
        payload = {
            "platform": p_platform,
            "skill": p_skill,
            "experience": p_exp,
            "project_type": p_type,
            "hours_billed": p_hours,
            "hourly_rate": p_rate,
            "client_rating": p_rating
        }
        pred_data, pred_err = safe_api_call(f"{BASE_URL}/predict", method="post", payload=payload)
        if pred_err:
            st.error(pred_err)
        else:
            prob = pred_data["probability"]
            label = pred_data["prediction"]  # 1 or 0
            est_value = p_hours * p_rate
            if label == 1:
                st.success(f"✅ **HIGH-VALUE project** — Probability: {prob:.1%}")
                st.balloons()
            else:
                st.warning(f"⚠️ **NOT high-value** — Probability: {prob:.1%}")
            st.write("**Input summary:**")
            summary_df = pd.DataFrame([payload])
            summary_df["estimated_value"] = f"${est_value:,.2f}"
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            st.info(
                f"💡 **NRA Insight:** Estimated project value = **${est_value:,.2f}** "
                f"({p_hours}h × ${p_rate}/hr). Model confidence: **{prob:.1%}**. "
                f"{'Proceed — strong high-value signal.' if label==1 else 'Reconsider scope: increase hours or hourly rate to cross the $5,000 threshold.'}"
            )