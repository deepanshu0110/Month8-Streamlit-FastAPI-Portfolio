# build_model.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

# ---------- 1. Generate data (same as Section 1) ----------
np.random.seed(141)
n = 500

categories = ['ML/AI', 'Web Dev', 'Data Analytics', 'Graphic Design',
              'Content Writing', 'SEO/Digital Marketing']   # ← correct name
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

# Introduce nulls
null_idx = np.random.choice(n, 25, replace=False)
df.loc[null_idx[:10],  'client_rating'] = np.nan
df.loc[null_idx[10:20],'bids_received'] = np.nan
df.loc[null_idx[20:],  'duration_days'] = np.nan

# ---------- 2. Create binary target ----------
df['target'] = (df['outcome'] == 'Completed').astype(int)

# ---------- 3. Handle missing values ----------
medians = {
    'client_rating': df['client_rating'].median(),
    'bids_received': df['bids_received'].median(),
    'duration_days': df['duration_days'].median()
}
df['client_rating'].fillna(medians['client_rating'], inplace=True)
df['bids_received'].fillna(medians['bids_received'], inplace=True)
df['duration_days'].fillna(medians['duration_days'], inplace=True)

# ---------- 4. Label encode categoricals ----------
cat_cols = ['category', 'platform', 'level']
le_dict = {}
for col in cat_cols:
    le = LabelEncoder()
    df[col+'_enc'] = le.fit_transform(df[col])
    le_dict[col] = le

# ---------- 5. Feature set ----------
feat_cols = ['budget_inr', 'duration_days', 'client_rating', 'bids_received',
             'category_enc', 'platform_enc', 'level_enc']
X = df[feat_cols]
y = df['target']

# ---------- 6. Train/test split (stratified) ----------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=141, stratify=y
)

# ---------- 7. Train Random Forest ----------
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=6,
    min_samples_leaf=5,
    random_state=141
)
model.fit(X_train, y_train)

# ---------- 8. Evaluate ----------
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]
acc = accuracy_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_proba)
cm = confusion_matrix(y_test, y_pred)

print(f"Test Accuracy : {acc:.4f}")      # Expect 0.6200
print(f"ROC-AUC       : {auc:.4f}")      # Expect 0.5108
print(f"Confusion Matrix:\n{cm}")        # Expect [[0,35],[3,62]]

# ---------- 9. Save model bundle (including X_test for SHAP) ----------
model_bundle = {
    'model': model,
    'le_dict': le_dict,
    'feat_cols': feat_cols,
    'medians': medians,
    'classes': {col: list(le_dict[col].classes_) for col in cat_cols},
    'accuracy': acc,
    'roc_auc': auc,
    'confusion_matrix': cm,
    'X_test': X_test   # <-- save test data for global SHAP
}
joblib.dump(model_bundle, 'day146_model.pkl')
print("\n✅ Model saved as 'day146_model.pkl'")