# utils/data_loader.py
import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def get_raw_data():
    """Generate the FreelanceHub dataset (500 rows, seed=141)."""
    np.random.seed(141)
    n = 500
    categories = ['ML/AI', 'Web Dev', 'Data Analytics',
                  'Graphic Design', 'Content Writing', 'SEO/Digital Marketing']
    platforms  = ['Upwork', 'Freelancer', 'Fiverr', 'Toptal', 'Direct Client']
    cities     = ['Mumbai', 'Bangalore', 'Delhi', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata']
    levels     = ['Entry', 'Mid', 'Senior']
    outcomes   = ['Completed', 'Cancelled', 'In Progress']
    months     = ['Jan','Feb','Mar','Apr','May','Jun',
                  'Jul','Aug','Sep','Oct','Nov','Dec']

    df = pd.DataFrame({
        'project_id':    [f'PJ{1000+i}' for i in range(n)],
        'category':      np.random.choice(categories, n),
        'platform':      np.random.choice(platforms, n, p=[0.30,0.25,0.25,0.10,0.10]),
        'city':          np.random.choice(cities, n),
        'level':         np.random.choice(levels, n, p=[0.40,0.40,0.20]),
        'budget_inr':    np.random.randint(5000, 120001, n),
        'duration_days': np.random.randint(7, 91, n).astype(float),
        'client_rating': np.round(np.random.uniform(2.5, 5.0, n), 1),
        'bids_received': np.random.randint(2, 51, n).astype(float),
        'outcome':       np.random.choice(outcomes, n, p=[0.65, 0.20, 0.15]),
        'month_posted':  np.random.choice(months, n),
    })
    # Intentional nulls (25 total)
    null_idx = np.random.choice(n, 25, replace=False)
    df.loc[null_idx[:10], 'client_rating'] = np.nan
    df.loc[null_idx[10:20], 'bids_received'] = np.nan
    df.loc[null_idx[20:], 'duration_days'] = np.nan
    return df

@st.cache_data
def get_summary_stats(df):
    """Return a dictionary of 5 key metrics."""
    total_projects = len(df)
    completed_pct = round((df['outcome'] == 'Completed').sum() / len(df) * 100, 1)
    avg_budget = round(df['budget_inr'].mean(), 0)
    top_platform = df.groupby('platform')['budget_inr'].mean().idxmax()
    null_count = int(df.isnull().sum().sum())
    return {
        'total_projects': total_projects,
        'completed_pct': completed_pct,
        'avg_budget': avg_budget,
        'top_platform': top_platform,
        'null_count': null_count
    }