import pytest
import pandas as pd
import numpy as np

def get_dataset():
    """Generate the FreelanceHub dataset (seed=141, 500 rows, 7 columns)."""
    np.random.seed(141)
    n = 500
    platforms        = np.random.choice(["Upwork","Fiverr","Freelancer","Toptal","PeoplePerHour"], n)
    categories       = np.random.choice(["Data Science","Web Dev","Design","Writing","Marketing"], n)
    experience_level = np.random.choice(["Junior","Mid","Senior"], n)
    hours_worked     = np.random.randint(5, 160, n)
    hourly_rate      = np.round(np.random.uniform(500, 5000, n), 2)
    client_rating    = np.round(np.random.uniform(3.0, 5.0, n), 1)
    revenue          = np.round(hours_worked * hourly_rate * np.random.uniform(0.8, 1.2, n), 2)
    return pd.DataFrame({
        "platform": platforms,
        "category": categories,
        "experience_level": experience_level,
        "hours_worked": hours_worked,
        "hourly_rate": hourly_rate,
        "client_rating": client_rating,
        "revenue": revenue
    })

def test_shape():
    df = get_dataset()
    assert df.shape == (500, 7)

def test_no_nulls():
    df = get_dataset()
    assert df.isnull().sum().sum() == 0

def test_revenue_positive():
    df = get_dataset()
    assert (df["revenue"] > 0).all()

def test_rating_range():
    df = get_dataset()
    assert df["client_rating"].between(3.0, 5.0).all()

def test_platform_unique_count():
    df = get_dataset()
    assert df["platform"].nunique() == 5
