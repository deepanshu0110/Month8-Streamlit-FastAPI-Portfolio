import streamlit as st

st.set_page_config(page_title="FreelanceHub Suite", layout="wide")

home = st.Page("app.py", title="Home", icon="🏠")
analysis = st.Page("pages/analysis_page.py", title="Analysis", icon="📊")
prediction = st.Page("pages/prediction_page.py", title="Prediction", icon="🤖")

pg = st.navigation({
    "Dashboard": [home],
    "Insights": [analysis],
    "Tools": [prediction]
})
pg.run()