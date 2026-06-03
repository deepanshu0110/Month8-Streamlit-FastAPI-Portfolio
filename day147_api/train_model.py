# train_model.py
import numpy as np
import pandas as pd
import os, json, joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

np.random.seed(141)
n = 500

categories      = ['Web Dev', 'Data Science', 'Graphic Design', 'Content Writing', 'SEO']
experience_lvls = ['Junior', 'Mid', 'Senior']
payment_types   = ['Fixed', 'Hourly']

df = pd.DataFrame({
    'project_id':       range(1, n+1),
    'category':         np.random.choice(categories, n),
    'experience_level': np.random.choice(experience_lvls, n),
    'hourly_rate':      np.round(np.random.uniform(5, 80, n), 2),
    'client_rating':    np.where(np.random.rand(n) < 0.08, np.nan,
                            np.round(np.random.uniform(1, 5, n), 1)),
    'bids_received':    np.where(np.random.rand(n) < 0.06, np.nan,
                            np.random.randint(1, 60, n).astype(float)),
    'payment_type':     np.random.choice(payment_types, n),
    'duration_days':    np.where(np.random.rand(n) < 0.05, np.nan,
                            np.random.randint(7, 120, n).astype(float)),
    'milestones':       np.random.randint(1, 10, n),
    'revision_rounds':  np.random.randint(0, 5, n),
    'project_status':   np.random.choice(['Completed', 'Cancelled'], n, p=[0.65, 0.35])
})

# Fill medians – corrected to avoid chained assignment warning
cr_median = df['client_rating'].median()
br_median = df['bids_received'].median()
dd_median = df['duration_days'].median()
df['client_rating'] = df['client_rating'].fillna(cr_median)
df['bids_received'] = df['bids_received'].fillna(br_median)
df['duration_days'] = df['duration_days'].fillna(dd_median)

# Label encoders
le_cat = LabelEncoder().fit(df['category'])
le_exp = LabelEncoder().fit(df['experience_level'])
le_pay = LabelEncoder().fit(df['payment_type'])
le_tgt = LabelEncoder().fit(df['project_status'])

df['category_enc']    = le_cat.transform(df['category'])
df['exp_enc']         = le_exp.transform(df['experience_level'])
df['payment_enc']     = le_pay.transform(df['payment_type'])
df['target']          = le_tgt.transform(df['project_status'])

FEATURES = ['hourly_rate','client_rating','bids_received','duration_days',
            'milestones','revision_rounds','category_enc','exp_enc','payment_enc']

X = df[FEATURES]
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=141)

model = RandomForestClassifier(n_estimators=100, random_state=141)
model.fit(X_train, y_train)

acc = accuracy_score(y_test, model.predict(X_test))

os.makedirs('day147_api', exist_ok=True)
joblib.dump(model,   'day147_api/model.pkl')
joblib.dump(le_cat,  'day147_api/le_cat.pkl')
joblib.dump(le_exp,  'day147_api/le_exp.pkl')
joblib.dump(le_pay,  'day147_api/le_pay.pkl')
joblib.dump(le_tgt,  'day147_api/le_tgt.pkl')

metadata = {
    "model": "RandomForestClassifier",
    "n_estimators": 100,
    "accuracy": round(acc, 4),
    "features": FEATURES,
    "target_classes": list(le_tgt.classes_),
    "fill_medians": {
        "client_rating": cr_median,
        "bids_received": br_median,
        "duration_days": dd_median
    },
    "category_encoding": dict(zip(le_cat.classes_, le_cat.transform(le_cat.classes_).tolist())),
    "experience_encoding": dict(zip(le_exp.classes_, le_exp.transform(le_exp.classes_).tolist())),
    "payment_encoding": dict(zip(le_pay.classes_, le_pay.transform(le_pay.classes_).tolist())),
    "training_rows": len(X_train),
    "test_rows": len(X_test)
}
with open('day147_api/metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print("✅ Model and artifacts saved to day147_api/")