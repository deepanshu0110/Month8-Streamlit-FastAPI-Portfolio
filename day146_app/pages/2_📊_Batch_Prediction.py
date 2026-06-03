# pages/2_📊_Batch_Prediction.py
import streamlit as st
import pandas as pd
import io
import joblib

st.set_page_config(page_title="Batch Prediction", page_icon="📊", layout="wide")

@st.cache_resource
def load_model():
    return joblib.load("day146_model.pkl")

bundle = load_model()
model = bundle['model']
le_dict = bundle['le_dict']
feat_cols = bundle['feat_cols']
medians = bundle['medians']
cat_cols = ['category', 'platform', 'level']

st.title("📊 Batch Prediction")
st.markdown("Upload a CSV file with the same columns as the training data. The app will predict completion status for all rows.")

uploaded = st.file_uploader("Upload project CSV", type=['csv'])

if uploaded:
    df = pd.read_csv(io.BytesIO(uploaded.read()))
    st.subheader("Preview (first 5 rows)")
    st.dataframe(df.head(5), use_container_width=True)
    
    # Fill nulls
    for col, val in medians.items():
        if col in df.columns:
            df[col].fillna(val, inplace=True)
    
    # Encode categoricals safely
    for col in cat_cols:
        if col in df.columns:
            try:
                df[col+'_enc'] = le_dict[col].transform(df[col].astype(str))
            except ValueError as e:
                st.error(f"Column '{col}' contains unseen labels: {e}")
                st.stop()
    
    missing = [c for c in feat_cols if c not in df.columns]
    if missing:
        st.error(f"Missing columns: {missing}")
    else:
        X = df[feat_cols]
        probs = model.predict_proba(X)[:, 1]
        preds = (probs >= 0.5).astype(int)
        df['predicted_outcome'] = ['Completed' if p==1 else 'Not Completed' for p in preds]
        df['confidence_pct'] = (probs * 100).round(1)
        
        st.subheader("Prediction Results")
        show_cols = ['project_id', 'category', 'platform', 'budget_inr', 
                     'predicted_outcome', 'confidence_pct']
        present_cols = [c for c in show_cols if c in df.columns]
        st.dataframe(df[present_cols].head(10), use_container_width=True)
        
        total = len(df)
        comp_pct = (df['predicted_outcome'] == 'Completed').mean() * 100
        avg_conf = df['confidence_pct'].mean()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Projects", total)
        col2.metric("Predicted Completed %", f"{comp_pct:.1f}%")
        col3.metric("Avg Confidence", f"{avg_conf:.1f}%")
        
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇ Download Predictions CSV",
            data=csv_bytes,
            file_name="freelancehub_predictions.csv",
            mime="text/csv"
        )
        st.success(f"✅ {total} predictions ready for download")