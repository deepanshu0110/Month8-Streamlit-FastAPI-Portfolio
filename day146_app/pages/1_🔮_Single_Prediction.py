# pages/1_🔮_Single_Prediction.py
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
import shap

st.set_page_config(page_title="Single Prediction", page_icon="🔮", layout="wide")

@st.cache_resource
def load_model():
    return joblib.load("day146_model.pkl")

bundle = load_model()
model = bundle['model']
le_dict = bundle['le_dict']
feat_cols = bundle['feat_cols']
medians = bundle['medians']
classes = bundle['classes']

st.title("🔮 Single Project Prediction")
st.markdown("Fill in the project details to see the predicted outcome and SHAP explanation.")

with st.form("prediction_form"):
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Category", classes['category'])
        platform = st.selectbox("Platform", classes['platform'])
        level = st.selectbox("Freelancer Level", classes['level'])
        budget = st.number_input("Budget (₹)", min_value=5000, max_value=120000, value=45000, step=1000)
    with col2:
        duration = st.slider("Duration (days)", 7, 90, 30)
        rating = st.slider("Client Rating", 2.5, 5.0, 4.2, 0.1)
        bids = st.slider("Bids Received", 2, 50, 15)
    
    submitted = st.form_submit_button("Predict")

if submitted:
    try:
        cat_enc = le_dict['category'].transform([category])[0]
        plat_enc = le_dict['platform'].transform([platform])[0]
        lvl_enc = le_dict['level'].transform([level])[0]
    except ValueError as e:
        st.error(f"Encoding error: {e}")
        st.stop()
    
    input_data = [[budget, duration, rating, bids, cat_enc, plat_enc, lvl_enc]]
    input_df = pd.DataFrame(input_data, columns=feat_cols)
    
    prob = model.predict_proba(input_df)[0][1]
    pred_class = "Completed" if prob >= 0.5 else "Not Completed"
    
    st.subheader("Prediction Result")
    if prob >= 0.70:
        st.success(f"✅ High confidence: {pred_class}")
        risk = "Low"
    elif prob >= 0.50:
        st.warning(f"⚠️ Moderate confidence: {pred_class}")
        risk = "Medium"
    else:
        st.error(f"❌ Low confidence: {pred_class}")
        risk = "High"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Prediction", pred_class)
    col2.metric("Confidence", f"{prob*100:.1f}%")
    col3.metric("Risk", risk)
    st.progress(int(prob*100))
    
    # ---------- Bonus: SHAP Waterfall ----------
    st.markdown("---")
    st.subheader("💡 Why this prediction? – SHAP Feature Contributions")
    explainer = shap.TreeExplainer(model)
    shap_vals = explainer.shap_values(input_df)
    
    # Extract contributions for class "Completed" (index 1)
    if isinstance(shap_vals, list):
        shap_contrib = shap_vals[1][0] if len(shap_vals) > 1 else shap_vals[0][0]
    elif shap_vals.ndim == 3:
        shap_contrib = shap_vals[0, :, 1]  # shape (1, n_features, 2)
    else:
        shap_contrib = shap_vals[0]
    
    # Ensure flat array
    if hasattr(shap_contrib, 'flatten'):
        shap_contrib = shap_contrib.flatten()
    
    shap_df = pd.DataFrame({
        'Feature': feat_cols,
        'SHAP Value': shap_contrib,
        'Color': ['#2ECC71' if x > 0 else '#E74C3C' for x in shap_contrib]
    }).sort_values('SHAP Value', ascending=False)
    
    fig = go.Figure(go.Bar(
        x=shap_df['SHAP Value'],
        y=shap_df['Feature'],
        orientation='h',
        marker_color=shap_df['Color'],
        text=shap_df['SHAP Value'].round(3),
        textposition='outside'
    ))
    fig.update_layout(
        title="SHAP Feature Contributions (positive = pushes toward Completed)",
        xaxis_title="SHAP Value",
        yaxis_title="Feature",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Green bars increase probability of completion; red bars decrease it.")