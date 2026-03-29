import pandas as pd
import numpy as np
import torch
import joblib
from collections import deque
from src.models.lstm_autoencoder import FEATURE_COLS, INPUT_DIM, LSTMAutoencoder
import yaml

with open("configs/config.yaml") as f:
    config = yaml.safe_load(f)

CFG = config["model"]["lstm_autoencoder"]
SEQ_LEN = CFG["sequence_length"]

# Load artifacts directly
model = LSTMAutoencoder(INPUT_DIM, CFG["hidden_dim"], CFG["latent_dim"])
model.load_state_dict(torch.load("saved_models/lstm_autoencoder.pt", map_location="cpu"))
model.eval()
scaler    = joblib.load("saved_models/lstm_scaler.pkl")
threshold = joblib.load("saved_models/lstm_threshold.pkl")

print(f"Threshold: {threshold}")
print(f"Scaler mean shape: {scaler.mean_.shape}")
print(f"Scaler expects n_features: {scaler.n_features_in_}")

# Load data and group by user
df = pd.read_csv('data/processed/features.csv').sort_values('timestamp')
df[FEATURE_COLS] = df[FEATURE_COLS].fillna(0)

# Pick a user with many events
user_counts = df.groupby('user_id').size().sort_values(ascending=False)
test_user = user_counts.index[0]
print(f"\nTest user: {test_user} ({user_counts[test_user]} events)")

user_df = df[df['user_id'] == test_user].reset_index(drop=True)
X = user_df[FEATURE_COLS].values.astype(np.float32)

# Build one sequence manually
seq = X[:SEQ_LEN]  # shape (10, 46)
print(f"Sequence shape: {seq.shape}")

# Scale it
flat = seq.reshape(-1, INPUT_DIM)  # (10*46? no — (10, 46))
print(f"Flat shape for scaler: {flat.shape}")

flat_s = scaler.transform(flat)
seq_s  = flat_s.reshape(1, SEQ_LEN, INPUT_DIM)

tensor = torch.tensor(seq_s.astype(np.float32))
with torch.no_grad():
    recon = model(tensor)
    mse = float(((recon - tensor)**2).mean().item())

print(f"MSE: {mse:.6f}")
print(f"Threshold: {threshold:.6f}")
print(f"Score (mse/threshold): {mse/threshold:.6f}")
print(f"Is anomaly (score>1.0): {mse > threshold}")

# Now check a known anomalous user
anomalous_users = df[df['is_anomalous']==1]['user_id'].unique()
print(f"\nChecking anomalous user: {anomalous_users[0]}")
anom_df = df[df['user_id']==anomalous_users[0]].reset_index(drop=True)
X_anom  = anom_df[FEATURE_COLS].values.astype(np.float32)

if len(X_anom) >= SEQ_LEN:
    seq2   = X_anom[:SEQ_LEN]
    flat2  = scaler.transform(seq2)
    seq_s2 = flat2.reshape(1, SEQ_LEN, INPUT_DIM)
    t2     = torch.tensor(seq_s2.astype(np.float32))
    with torch.no_grad():
        r2   = model(t2)
        mse2 = float(((r2 - t2)**2).mean().item())
    print(f"Anomalous user MSE: {mse2:.6f} (threshold={threshold:.6f})")
else:
    print(f"Not enough events ({len(X_anom)}) for sequence")