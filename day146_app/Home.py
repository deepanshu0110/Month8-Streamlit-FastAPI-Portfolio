# Home.py
import streamlit as st
import joblib

st.set_page_config(page_title="FreelanceHub Predictor", page_icon="🔮", layout="wide")

@st.cache_resource
def load_model():
    return joblib.load("day146_model.pkl")

bundle = load_model()

st.title("🔮 FreelanceHub Project Completion Predictor")
st.markdown("**Explainable ML Dashboard** – Predict project outcome, understand why, and batch-score your projects.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Accuracy", f"{bundle['accuracy']*100:.1f}%")
col2.metric("ROC-AUC", f"{bundle['roc_auc']:.4f}")
col3.metric("Training rows", "400")
col4.metric("Test rows", "100")

st.info("This app predicts whether a freelance project will be **Completed** or not. Enter a single project in *Single Prediction*, upload many in *Batch Prediction*, or explore model performance in *Model Performance*.")

st.warning("⚠️ **Model AUC = 0.51 – near-random**. Use predictions with caution. This dashboard demonstrates ML deployment and explainability patterns, not a production-ready model.")