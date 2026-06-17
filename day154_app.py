# day154_app.py
# Streamlit + SQLite Integration – FreelanceHub Project Management
# Implements: Database setup, caching, CRUD, CSV bulk import, filter, NRA, audit log.

import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import datetime
import io

# ------------------------------------------------
# T1: Database setup – Engine + initial seeding
# ------------------------------------------------
@st.cache_resource
def get_engine():
    """Return SQLAlchemy engine (cached as resource)."""
    return create_engine("sqlite:///freelancehub.db", echo=False)

def init_db():
    """Create table and seed initial data if not exists."""
    engine = get_engine()
    inspector = inspect(engine)
    if not inspector.has_table("projects"):
        # Generate the raw DataFrame (same as Section 1)
        np.random.seed(141)
        n = 500
        categories = ['ML/AI', 'Web Dev', 'Data Analytics', 'Graphic Design',
                      'Content Writing', 'SEO/Digital Marketing']
        platforms  = ['Upwork', 'Freelancer', 'Fiverr', 'Toptal', 'Direct Client']
        cities     = ['Mumbai', 'Bangalore', 'Delhi', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata']
        levels     = ['Entry', 'Mid', 'Senior']
        outcomes   = ['Completed', 'Cancelled', 'In Progress']
        df = pd.DataFrame({
            'project_id':    [f'PJ{1000+i}' for i in range(n)],
            'category':      np.random.choice(categories, n),
            'platform':      np.random.choice(platforms, n, p=[0.30, 0.25, 0.25, 0.10, 0.10]),
            'city':          np.random.choice(cities, n),
            'level':         np.random.choice(levels, n, p=[0.40, 0.40, 0.20]),
            'budget_inr':    np.random.randint(5000, 120001, n),
            'duration_days': np.random.randint(7, 91, n),
            'client_rating': np.round(np.random.uniform(2.5, 5.0, n), 1),
            'bids_received': np.random.randint(2, 51, n),
            'outcome':       np.random.choice(outcomes, n, p=[0.65, 0.20, 0.15]),
            'month_posted':  np.random.choice(['Jan','Feb','Mar','Apr','May','Jun',
                                               'Jul','Aug','Sep','Oct','Nov','Dec'], n),
        })
        null_idx = np.random.choice(n, 25, replace=False)
        df.loc[null_idx[:10],  'client_rating'] = np.nan
        df.loc[null_idx[10:20],'bids_received'] = np.nan
        df.loc[null_idx[20:],  'duration_days'] = np.nan
        df.to_sql("projects", engine, if_exists="replace", index=False)
        st.info("Database seeded with 500 rows.")
    # Also create audit_log table if not exists
    if not inspector.has_table("audit_log"):
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT,
                    action TEXT,
                    project_id TEXT,
                    detail TEXT
                )
            """))
            conn.commit()

# ------------------------------------------------
# T2: Caching – load_projects with st.cache_data
# ------------------------------------------------
@st.cache_data(ttl=60)
def load_projects(_engine, category=None, platform=None, outcome=None):
    """
    Load projects from DB with optional filters.
    _engine is ignored for caching (underscore prefix).
    """
    conditions = []
    params = {}
    if category is not None:
        conditions.append("category = :category")
        params["category"] = category
    if platform is not None:
        conditions.append("platform = :platform")
        params["platform"] = platform
    if outcome is not None:
        conditions.append("outcome = :outcome")
        params["outcome"] = outcome

    if not conditions:
        query = "SELECT * FROM projects"
    else:
        query = "SELECT * FROM projects WHERE " + " AND ".join(conditions)
    return pd.read_sql(text(query), _engine, params=params)

def clear_project_cache():
    """Invalidate cached project data."""
    load_projects.clear()

# ------------------------------------------------
# T3: CRUD operations with parameterized queries
# Each write function clears the cache itself (self-contained)
# ------------------------------------------------
def insert_project(engine, row: dict):
    """Insert a single project using bound parameters."""
    query = text("""
        INSERT INTO projects (
            project_id, category, platform, city, level,
            budget_inr, duration_days, client_rating, bids_received,
            outcome, month_posted
        ) VALUES (
            :project_id, :category, :platform, :city, :level,
            :budget_inr, :duration_days, :client_rating, :bids_received,
            :outcome, :month_posted
        )
    """)
    with engine.begin() as conn:
        conn.execute(query, row)
    log_action(engine, "INSERT", row["project_id"], f"Inserted by user")
    clear_project_cache()   # <- self-contained cache clearing

def update_outcome(engine, project_id: str, new_outcome: str):
    """Update outcome of a project."""
    query = text("UPDATE projects SET outcome = :outcome WHERE project_id = :pid")
    with engine.begin() as conn:
        result = conn.execute(query, {"outcome": new_outcome, "pid": project_id})
        if result.rowcount == 0:
            raise ValueError(f"Project {project_id} not found.")
    log_action(engine, "UPDATE", project_id, f"Outcome changed to {new_outcome}")
    clear_project_cache()   # <- self-contained

def delete_project(engine, project_id: str):
    """Delete a project by project_id."""
    query = text("DELETE FROM projects WHERE project_id = :pid")
    with engine.begin() as conn:
        result = conn.execute(query, {"pid": project_id})
        if result.rowcount == 0:
            raise ValueError(f"Project {project_id} not found.")
    log_action(engine, "DELETE", project_id, "Deleted")
    clear_project_cache()   # <- self-contained

# ------------------------------------------------
# Bonus: Audit log
# ------------------------------------------------
def log_action(engine, action: str, project_id: str, detail: str):
    """Write to audit_log table."""
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO audit_log (ts, action, project_id, detail) VALUES (:ts, :action, :pid, :detail)"),
            {
                "ts": datetime.datetime.now().isoformat(),
                "action": action,
                "pid": project_id,
                "detail": detail
            }
        )

def get_recent_audit(engine, limit=5):
    """Return the most recent audit entries."""
    return pd.read_sql(
        text("SELECT ts, action, project_id, detail FROM audit_log ORDER BY id DESC LIMIT :lim"),
        engine,
        params={"lim": limit}
    )

# ------------------------------------------------
# T4: CSV bulk import
# ------------------------------------------------
EXPECTED_COLUMNS = {
    'project_id', 'category', 'platform', 'city', 'level',
    'budget_inr', 'duration_days', 'client_rating', 'bids_received',
    'outcome', 'month_posted'
}

def bulk_import(engine, df: pd.DataFrame):
    """Insert all rows from a DataFrame in one transaction."""
    # Validate columns
    if set(df.columns) != EXPECTED_COLUMNS:
        missing = EXPECTED_COLUMNS - set(df.columns)
        extra = set(df.columns) - EXPECTED_COLUMNS
        raise ValueError(f"Column mismatch. Missing: {missing}, Extra: {extra}")
    # Clean data: ensure proper types
    df = df.copy()
    for col in ['budget_inr', 'duration_days', 'client_rating', 'bids_received']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # Insert with to_sql (append)
    with engine.begin() as conn:
        df.to_sql("projects", conn, if_exists="append", index=False)
    # Audit log each row
    for pid in df['project_id']:
        log_action(engine, "BULK_INSERT", pid, "Imported via CSV")
    clear_project_cache()   # <- self-contained

# ------------------------------------------------
# T5: Parameterized filter
# ------------------------------------------------
def filter_projects(engine, category=None, platform=None, outcome=None):
    """Dynamic WHERE clause with bound parameters."""
    conditions = []
    params = {}
    if category is not None:
        conditions.append("category = :category")
        params["category"] = category
    if platform is not None:
        conditions.append("platform = :platform")
        params["platform"] = platform
    if outcome is not None:
        conditions.append("outcome = :outcome")
        params["outcome"] = outcome
    if not conditions:
        query = "SELECT * FROM projects"
    else:
        query = "SELECT * FROM projects WHERE " + " AND ".join(conditions)
    return pd.read_sql(text(query), engine, params=params)

# ------------------------------------------------
# T6: NRA insight – cancellation rate by platform
# ------------------------------------------------
def cancellation_rate_by_platform(engine):
    """Return a DataFrame with platform, total, cancelled, and rate."""
    query = text("""
        SELECT
            platform,
            COUNT(*) AS total,
            SUM(CASE WHEN outcome = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled
        FROM projects
        GROUP BY platform
    """)
    df = pd.read_sql(query, engine)
    df['rate'] = (df['cancelled'] / df['total'] * 100).round(2)
    return df

# ------------------------------------------------
# Streamlit UI
# ------------------------------------------------
def main():
    st.set_page_config(page_title="FreelanceHub Admin", layout="wide")
    st.title("🗄️ FreelanceHub Project Manager")

    # Initialize DB
    init_db()
    engine = get_engine()

    # Sidebar: Recent Activity (Bonus)
    with st.sidebar:
        st.header("📋 Recent Activity")
        try:
            audit_df = get_recent_audit(engine)
            if not audit_df.empty:
                for _, row in audit_df.iterrows():
                    st.caption(f"**{row['action']}** {row['project_id']} at {row['ts'][:16]}")
                    st.caption(f"_{row['detail']}_")
                    st.divider()
            else:
                st.info("No activity yet.")
        except Exception:
            st.info("No audit log table yet.")

    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", "➕ Add/Edit", "📂 Bulk Import", "🔍 Filter", "📈 NRA Insight"
    ])

    # --- Tab 1: Dashboard ---
    with tab1:
        st.subheader("Current Projects")
        try:
            df = load_projects(engine)
            st.metric("Total Projects", len(df))
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading data: {e}")

    # --- Tab 2: Add/Edit/Delete ---
    with tab2:
        st.subheader("Add New Project")
        with st.form("add_project_form"):
            col1, col2 = st.columns(2)
            with col1:
                pid = st.text_input("Project ID", "PJ2000")
                cat = st.selectbox("Category", ['ML/AI','Web Dev','Data Analytics','Graphic Design','Content Writing','SEO/Digital Marketing'])
                plat = st.selectbox("Platform", ['Upwork','Freelancer','Fiverr','Toptal','Direct Client'])
                city = st.selectbox("City", ['Mumbai','Bangalore','Delhi','Hyderabad','Chennai','Pune','Kolkata'])
                lvl = st.selectbox("Level", ['Entry','Mid','Senior'])
            with col2:
                budget = st.number_input("Budget (INR)", min_value=0, value=75000, step=1000)
                dur = st.number_input("Duration (days)", min_value=1, value=30)
                rating = st.number_input("Client Rating", min_value=0.0, max_value=5.0, value=4.8, step=0.1)
                bids = st.number_input("Bids Received", min_value=0, value=12)
                outcome = st.selectbox("Outcome", ['Completed','Cancelled','In Progress'])
                month = st.selectbox("Month Posted", ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
            submitted = st.form_submit_button("Add Project")
            if submitted:
                try:
                    row = {
                        "project_id": pid,
                        "category": cat,
                        "platform": plat,
                        "city": city,
                        "level": lvl,
                        "budget_inr": budget,
                        "duration_days": dur,
                        "client_rating": rating,
                        "bids_received": bids,
                        "outcome": outcome,
                        "month_posted": month
                    }
                    insert_project(engine, row)   # clears its own cache
                    st.success(f"Project {pid} added successfully.")
                    st.rerun()   # force immediate refresh of the Dashboard
                except Exception as e:
                    st.error(f"Error: {e}")

        st.subheader("Update Outcome")
        with st.form("update_form"):
            pid_update = st.text_input("Project ID to update", "PJ1100")
            new_outcome = st.selectbox("New Outcome", ['Completed','Cancelled','In Progress'])
            upd_submitted = st.form_submit_button("Update")
            if upd_submitted:
                try:
                    update_outcome(engine, pid_update, new_outcome)   # clears its own cache
                    st.success(f"Project {pid_update} updated to {new_outcome}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        st.subheader("Delete Project")
        with st.form("delete_form"):
            pid_del = st.text_input("Project ID to delete", "PJ1250")
            del_submitted = st.form_submit_button("Delete")
            if del_submitted:
                try:
                    delete_project(engine, pid_del)   # clears its own cache
                    st.success(f"Project {pid_del} deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- Tab 3: Bulk Import ---
    with tab3:
        st.subheader("Bulk CSV Import")
        uploaded = st.file_uploader("Upload CSV with columns matching projects schema", type=["csv"])
        if uploaded is not None:
            try:
                df_import = pd.read_csv(io.BytesIO(uploaded.read()))
                st.dataframe(df_import.head(), use_container_width=True)
                if st.button("Import Bulk Data"):
                    bulk_import(engine, df_import)   # clears its own cache
                    st.success(f"Imported {len(df_import)} rows successfully.")
                    st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")

    # --- Tab 4: Filter ---
    with tab4:
        st.subheader("Filter Projects")
        cat_filter = st.selectbox("Category", [None] + ['ML/AI','Web Dev','Data Analytics','Graphic Design','Content Writing','SEO/Digital Marketing'])
        plat_filter = st.selectbox("Platform", [None] + ['Upwork','Freelancer','Fiverr','Toptal','Direct Client'])
        out_filter = st.selectbox("Outcome", [None] + ['Completed','Cancelled','In Progress'])
        if st.button("Apply Filter"):
            try:
                filtered = filter_projects(engine, category=cat_filter, platform=plat_filter, outcome=out_filter)
                st.metric("Rows Found", len(filtered))
                st.dataframe(filtered, use_container_width=True)
            except Exception as e:
                st.error(f"Filter error: {e}")

    # --- Tab 5: NRA Insight ---
    with tab5:
        st.subheader("Cancellation Rate by Platform")
        try:
            rate_df = cancellation_rate_by_platform(engine)
            st.dataframe(rate_df, use_container_width=True)
            top = rate_df.loc[rate_df['rate'].idxmax()]
            overall = rate_df['cancelled'].sum() / rate_df['total'].sum() * 100

            # Get average budget for the top platform (for the Reason)
            avg_budget_df = pd.read_sql("SELECT platform, AVG(budget_inr) AS avg_budget FROM projects GROUP BY platform", engine)
            top_avg_budget = avg_budget_df[avg_budget_df['platform'] == top['platform']]['avg_budget'].values[0]

            st.write(f"**Highest:** {top['platform']} – {top['rate']:.2f}% cancellation rate")
            st.write(f"**Overall cancellation rate:** {overall:.2f}%")

            st.subheader("📌 NRA Insight")
            st.markdown(f"""
            **Number**  : {top['platform']} has the highest cancellation rate at **{top['rate']:.2f}%**, 
                           well above the overall rate of {overall:.2f}%.

            **Reason**  : Toptal positions itself as a premium, invite‑only network, attracting 
                           high‑budget, complex projects (avg budget ₹{top_avg_budget:,.0f}). 
                           Clients on Toptal have higher expectations and stricter requirements; 
                           when projects fail to meet those expectations, cancellations are more 
                           frequent than on lower‑tier platforms.

            **Action**  : Introduce a mandatory project validation step for Toptal projects: 
                           require a minimum budget of ₹50,000 and at least 3 client reviews 
                           before the project is listed. This will filter out high‑risk projects.
            """)
        except Exception as e:
            st.error(f"Could not compute NRA: {e}")

if __name__ == "__main__":
    main()