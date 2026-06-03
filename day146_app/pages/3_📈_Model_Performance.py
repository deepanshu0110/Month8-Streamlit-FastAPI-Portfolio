# pages/3_📈_Model_Performance.py
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import shap

st.set_page_config(page_title="Model Performance", page_icon="📈", layout="wide")

@st.cache_resource
def load_model():
    return joblib.load("day146_model.pkl")

bundle = load_model()
model = bundle['model']
feat_cols = bundle['feat_cols']
cm = bundle['confusion_matrix']
tn, fp, fn, tp = cm.ravel()
X_test = bundle.get('X_test', None)  # saved from build_model

st.title("📈 Model Performance & Explainability")

# 1. Confusion Matrix
st.subheader("Confusion Matrix")
cm_df = pd.DataFrame([[tn, fp], [fn, tp]],
                     index=["Actual: Not Completed", "Actual: Completed"],
                     columns=["Predicted: Not Completed", "Predicted: Completed"])
fig_cm = px.imshow(cm_df.values, x=cm_df.columns, y=cm_df.index,
                   text_auto=True, color_continuous_scale="Blues", aspect="auto")
fig_cm.update_layout(height=400)
st.plotly_chart(fig_cm, use_container_width=True)

# 2. Feature Importance (Random Forest)
st.subheader("Feature Importance (Random Forest)")
importances = model.feature_importances_
fi_df = pd.DataFrame({'Feature': feat_cols, 'importance': importances}).sort_values('importance', ascending=True)
fig_fi = px.bar(fi_df, x='importance', y='Feature', orientation='h',
                color_discrete_sequence=['#1F3864'],
                title="Gini Importance – What the Model Learns")
st.plotly_chart(fig_fi, use_container_width=True)

# 3. Global SHAP (using X_test from bundle)
st.subheader("Global SHAP – Mean |SHAP|")
if X_test is not None:
    # Use a sample of test data for speed (max 100 rows)
    X_sample = X_test.sample(min(100, len(X_test)), random_state=141)
else:
    # Fallback: generate random data (should not happen if build_model is correct)
    np.random.seed(141)
    X_sample = pd.DataFrame(np.random.rand(50, len(feat_cols)), columns=feat_cols)
    st.warning("X_test not found in model bundle – using random sample for SHAP.")

explainer = shap.TreeExplainer(model)
shap_vals = explainer.shap_values(X_sample)

# Handle different output shapes
if isinstance(shap_vals, list):
    shap_array = np.abs(shap_vals[1]).mean(axis=0)
elif shap_vals.ndim == 3:
    shap_array = np.abs(shap_vals[:, :, 1]).mean(axis=0)
else:
    shap_array = np.abs(shap_vals).mean(axis=0)

if len(shap_array) != len(feat_cols):
    st.error(f"SHAP output length {len(shap_array)} != feature count {len(feat_cols)}")
else:
    shap_df = pd.DataFrame({'Feature': feat_cols, 'mean_shap': shap_array}).sort_values('mean_shap', ascending=True)
    fig_shap = px.bar(shap_df, x='mean_shap', y='Feature', orientation='h',
                      color_discrete_sequence=['#2C3E50'],
                      title="Mean |SHAP| – What Drives Predictions (SHAP)")
    st.plotly_chart(fig_shap, use_container_width=True)

# 4. NRA Insights
with st.expander("📝 Business Insights (NRA)"):
    st.markdown("""
    ### NRA 1 – Model Quality
    **Number:** ROC-AUC = **0.5108**  
    **Reason:** An AUC of 0.51 means the model discriminates barely better than random guessing. This happens because the dataset is highly imbalanced (65% Completed) and the model defaults to predicting the majority class.  
    **Action:** Apply **SMOTE** to oversample the minority class or use **class_weight='balanced'** in the Random Forest. Retrain and re-evaluate.

    ### NRA 2 – Top SHAP Feature
    **Number:** `category` has mean |SHAP| = **0.033** – highest among all 7 features by SHAP analysis.  
    **Reason:** Project type (ML/AI vs Content Writing) is the strongest driver of completion probability, not number of bids. SHAP measures real contribution to model predictions, while Gini importance only measures tree splits.  
    **Action:** Focus bids on **ML/AI and Data Analytics** categories where completion rates are highest. Use the batch prediction tool to filter projects with confidence >70% in these categories.
    """)