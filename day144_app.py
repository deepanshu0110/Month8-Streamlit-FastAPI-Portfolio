# day144_app.py
# Streamlit ML Deployment: Project Completion Predictor for FreelanceHub India

import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import joblib

# ------------------------------------------------------------------------------
# Page configuration
st.set_page_config(page_title="FreelanceHub ML Predictor", layout="wide")
st.title("🤖 FreelanceHub Project Completion Predictor")
st.caption("Predicts whether a project will be Completed or Cancelled based on project features.")

# ------------------------------------------------------------------------------
# T1: Load model bundle with @st.cache_resource (10 pts)
@st.cache_resource
def load_model():
    """Load the trained model, label encoders, and feature columns."""
    try:
        bundle = joblib.load("freelancehub_model.pkl")
        return bundle
    except FileNotFoundError:
        st.error("❌ Model file 'freelancehub_model.pkl' not found. Please run the training script first.")
        st.stop()

bundle = load_model()
model = bundle["model"]
le_dict = bundle["le_dict"]
feature_cols = bundle["feature_cols"]
cat_cols = bundle["cat_cols"]
classes = bundle["classes"]

# ------------------------------------------------------------------------------
# T2: Sidebar input widgets (15 pts)
st.sidebar.header("📝 Project Details")

budget = st.sidebar.slider("Budget (₹)", min_value=5000, max_value=150000, value=50000, step=1000)
duration = st.sidebar.slider("Duration (days)", min_value=3, max_value=90, value=30)
client_rating = st.sidebar.slider("Client Rating", min_value=2.5, max_value=5.0, value=4.0, step=0.1)
platform_fee = st.sidebar.selectbox("Platform Fee (%)", options=[10, 15, 20], index=1)  # default 15

category = st.sidebar.selectbox("Category", options=classes["category"])
freelancer_level = st.sidebar.selectbox("Freelancer Level", options=classes["freelancer_level"])
city = st.sidebar.selectbox("City", options=classes["city"])
month = st.sidebar.selectbox("Month", options=classes["month"])

# Encode categoricals using saved label encoders
category_enc = le_dict["category"].transform([category])[0]
level_enc = le_dict["freelancer_level"].transform([freelancer_level])[0]
city_enc = le_dict["city"].transform([city])[0]
month_enc = le_dict["month"].transform([month])[0]

# Build input DataFrame with EXACT column order as training
input_data = [[
    budget, duration, client_rating, platform_fee,
    category_enc, level_enc, city_enc, month_enc
]]
input_df = pd.DataFrame(input_data, columns=feature_cols)

# ------------------------------------------------------------------------------
# T3: Single prediction + probability display (15 pts)
prob = model.predict_proba(input_df)[0]   # [P(Cancelled), P(Completed)]
pred_class = model.predict(input_df)[0]   # 0 = Cancelled, 1 = Completed

# Probability values
prob_cancelled = prob[0]
prob_completed = prob[1]

# ------------------------------------------------------------------------------
# Bonus: replace st.progress with Plotly gauge chart (10★)
# Instead of a plain progress bar, we use a Plotly gauge.
# But we keep st.metric as well.
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=prob_completed * 100,
    title={"text": "Completion Probability (%)"},
    delta={"reference": 50},       # shows +/- vs 50%
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": "#1F3864"},
        "steps": [
            {"range": [0, 40], "color": "#FCE4D6"},   # red zone (high risk)
            {"range": [40, 70], "color": "#FFF2CC"},  # amber zone
            {"range": [70, 100], "color": "#E2EFDA"}, # green zone
        ],
        "threshold": {
            "line": {"color": "red", "width": 4},
            "thickness": 0.75,
            "value": 60              # decision boundary
        }
    }
))
fig_gauge.update_layout(height=300)

# ------------------------------------------------------------------------------
# T5: Model metrics tab (10 pts) – we'll create tabs first
tab1, tab2, tab3 = st.tabs(["🔮 Predict", "📊 Model Metrics", "📁 Batch Predict"])

with tab1:
    st.subheader("🔍 Prediction Result")
    col_left, col_right = st.columns([2, 1])
    with col_left:
        # Show gauge
        st.plotly_chart(fig_gauge, use_container_width=True)
        # Show numeric probability metric
        st.metric("Completion Probability", f"{prob_completed:.1%}")
    with col_right:
        # Colour-coded label
        if prob_completed >= 0.60:
            st.success("✅ Likely COMPLETED")
        else:
            st.error("⚠️ Risk of CANCELLATION")
        st.caption(f"P(Cancelled) = {prob_cancelled:.1%}")

with tab2:
    st.subheader("📈 Model Performance Metrics")
    # Test accuracy (from training notebook)
    st.metric("Test Accuracy", "88.89%")
    
    # Classification report table
    report_data = {
        "Class": ["Cancelled", "Completed"],
        "Precision": ["0.00", "0.89"],
        "Recall": ["0.00", "1.00"],
        "F1-Score": ["0.00", "0.94"],
        "Support": ["8", "64"]
    }
    report_df = pd.DataFrame(report_data)
    st.table(report_df)
    
    # Imbalance insight warning
    st.warning(
        "⚠️ **Class imbalance insight:** The model achieves 88.89% accuracy but never predicts Cancellation "
        "(recall = 0.00). This is because only 42 out of 358 projects are Cancelled (11.7%). The model learns "
        "to always predict Completed. In a real deployment, apply SMOTE or lower the prediction threshold "
        "to flag at-risk projects."
    )

    # T4: Feature importance bar chart (15 pts)
    st.subheader("🔑 Feature Importances")
    importances = model.feature_importances_
    imp_df = pd.DataFrame({"Feature": feature_cols, "Importance": importances})
    imp_df = imp_df.sort_values("Importance", ascending=True)  # horizontal bar needs ascending
    fig_imp = px.bar(
        imp_df,
        x="Importance",
        y="Feature",
        orientation="h",
        color_discrete_sequence=["#1F3864"],
        title="What Drives Project Completion? (Higher = More Influence)"
    )
    fig_imp.update_layout(yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig_imp, use_container_width=True)

with tab3:
    st.subheader("📂 Batch Predictions on Multiple Projects")
    st.markdown("Upload a CSV file with the following columns: `category`, `budget_inr`, `duration_days`, `client_rating`, `freelancer_level`, `city`, `platform_fee_pct`, `month`")
    
    uploaded_file = st.file_uploader("Upload project CSV", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df_batch = pd.read_csv(io.BytesIO(uploaded_file.read()))
            # Check required columns
            required_cols = ['category', 'budget_inr', 'duration_days', 'client_rating',
                             'freelancer_level', 'city', 'platform_fee_pct', 'month']
            missing = [c for c in required_cols if c not in df_batch.columns]
            if missing:
                st.error(f"Missing columns: {missing}")
            else:
                # Encode categoricals using saved encoders
                for col in cat_cols:
                    df_batch[col + '_enc'] = le_dict[col].transform(df_batch[col])
                # Select features in correct order
                X_batch = df_batch[feature_cols]
                # Predict
                preds = model.predict(X_batch)
                probs = model.predict_proba(X_batch)[:, 1]  # P(Completed)
                df_batch['predicted_status'] = np.where(preds == 1, "Completed", "Cancelled")
                df_batch['completion_probability'] = probs.round(4)
                # Show preview
                st.dataframe(df_batch.head(10), use_container_width=True)
                # Download button
                csv_bytes = df_batch.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download Predictions",
                    data=csv_bytes,
                    file_name="batch_predictions.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Error processing file: {e}")

# ------------------------------------------------------------------------------
# T7: NRA Insight (5 pts) – displayed in the main area after tabs
st.markdown("---")
st.subheader("📌 NRA Insight: Managing Project Completion Risk")
st.markdown("""
**Number:** The model achieves **88.89% accuracy**, with `platform_fee_pct` as the strongest predictor (importance = **0.24**).  
**Reason:** Only **11.7%** of projects are Cancelled (42 out of 358). The model never predicts cancellation (recall = 0.00) – it always chooses "Completed" because that maximises accuracy.  
**Action:** Lower the prediction threshold from 0.50 to **0.30**. Flag any project with P(Completed) < 0.70 for manual review. Alternatively, retrain with **SMOTE** to synthetically balance the classes, and set a minimum fee discount for high-budget projects to reduce cancellation risk.
""")