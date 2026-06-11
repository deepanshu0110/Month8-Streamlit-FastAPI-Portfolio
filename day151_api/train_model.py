# train_model.py
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

np.random.seed(141)
n = 500
platforms     = np.random.choice(['Upwork','Freelancer','Fiverr','Toptal'], n, p=[0.35,0.30,0.25,0.10])
skills        = np.random.choice(['Python','SQL','ML','Tableau','Excel','NLP'], n, p=[0.25,0.20,0.20,0.15,0.10,0.10])
experience    = np.random.choice(['Junior','Mid','Senior','Expert'], n, p=[0.25,0.35,0.25,0.15])
project_type  = np.random.choice(['Fixed','Hourly'], n, p=[0.55,0.45])
hours_billed  = np.random.randint(5, 201, n)
hourly_rate   = np.round(np.random.uniform(10, 100, n), 2)
client_rating = np.round(np.random.uniform(2.5, 5.0, n), 1)
status        = np.random.choice(['Completed','In Progress','Cancelled'], n, p=[0.60,0.25,0.15])
project_value = np.round(hours_billed * hourly_rate, 2)
high_value    = (project_value > 5000).astype(int)

df = pd.DataFrame({
    'project_id'   : range(1, n+1),
    'platform'     : platforms,
    'skill'        : skills,
    'experience'   : experience,
    'project_type' : project_type,
    'hours_billed' : hours_billed,
    'hourly_rate'  : hourly_rate,
    'client_rating': client_rating,
    'status'       : status,
    'project_value': project_value,
    'high_value'   : high_value
})

# Label encoders
le_platform = LabelEncoder().fit(df['platform'])
le_skill    = LabelEncoder().fit(df['skill'])
le_exp      = LabelEncoder().fit(df['experience'])
le_type     = LabelEncoder().fit(df['project_type'])

df['platform_enc'] = le_platform.transform(df['platform'])
df['skill_enc']    = le_skill.transform(df['skill'])
df['exp_enc']      = le_exp.transform(df['experience'])
df['type_enc']     = le_type.transform(df['project_type'])

features = ['hours_billed', 'hourly_rate', 'client_rating',
            'platform_enc', 'skill_enc', 'exp_enc', 'type_enc']
X = df[features]
y = df['high_value']

model = RandomForestClassifier(n_estimators=100, random_state=141)
model.fit(X, y)

joblib.dump(model, 'day149_model.pkl')
joblib.dump({
    'le_platform': le_platform,
    'le_skill': le_skill,
    'le_exp': le_exp,
    'le_type': le_type,
    'features': features
}, 'day149_encoders.pkl')

print("✅ Model and encoders saved.")