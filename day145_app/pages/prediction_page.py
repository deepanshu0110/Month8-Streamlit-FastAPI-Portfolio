# pages/2_🤖_Prediction.py
import streamlit as st

st.title("🤖 Budget Tier Classifier")
st.markdown("Estimate project budget tier based on client rating, duration, and bids received.")

# ── Sidebar inputs ─────────────────────────────────────────────────
with st.sidebar:
    st.subheader("📝 Project Parameters")
    duration = st.number_input("Duration (days)", min_value=7, max_value=90, value=30, step=1)
    bids = st.number_input("Bids Received", min_value=2, max_value=50, value=20, step=1)
    rating = st.number_input("Client Rating (1.0–5.0)", min_value=1.0, max_value=5.0, value=4.0, step=0.1)

# ── Rule-based classifier ─────────────────────────────────────────
def classify_tier(duration, bids, rating):
    if rating >= 4.0 and duration >= 30 and bids <= 20:
        return ("Premium (₹80k–₹1.2L)", "success")
    elif rating >= 3.5 and duration >= 15:
        return ("Mid-Range (₹40k–₹80k)", "warning")
    else:
        return ("Standard (₹5k–₹40k)", "error")

# ── Predict button + session state history ────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

if st.button("🔮 Predict Budget Tier"):
    tier, style = classify_tier(duration, bids, rating)
    # Store prediction
    st.session_state.history.insert(0, {
        "Duration (days)": duration,
        "Bids Received": bids,
        "Rating": rating,
        "Predicted Tier": tier
    })
    # Keep only last 5
    st.session_state.history = st.session_state.history[:5]

    # Display current prediction
    if style == "success":
        st.success(f"✅ Predicted Tier: **{tier}**")
    elif style == "warning":
        st.warning(f"⚠️ Predicted Tier: **{tier}**")
    else:
        st.error(f"❌ Predicted Tier: **{tier}**")

# ── Show history table ────────────────────────────────────────────
st.subheader("📜 Last 5 Predictions")
if st.session_state.history:
    st.dataframe(st.session_state.history, use_container_width=True)
else:
    st.info("No predictions yet – click the button above.")