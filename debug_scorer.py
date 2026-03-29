import pandas as pd
import numpy as np
import torch
import joblib
from src.models.lstm_autoencoder import FEATURE_COLS, INPUT_DIM, LSTMAutoencoder
import yaml

with open("configs/config.yaml") as f:
    config = yaml.safe_load(f)

CFG     = config["model"]["lstm_autoencoder"]
SEQ_LEN = CFG["sequence_length"]

model = LSTMAutoencoder(INPUT_DIM, CFG["hidden_dim"], CFG["latent_dim"])
model.load_state_dict(torch.load("saved_models/lstm_autoencoder.pt", map_location="cpu"))
model.eval()
scaler    = joblib.load("saved_models/lstm_scaler.pkl")
threshold = joblib.load("saved_models/lstm_threshold.pkl")

print(f"Threshold: {threshold:.4f}")

df = pd.read_csv('data/processed/features.csv').sort_values('timestamp')
df[FEATURE_COLS] = df[FEATURE_COLS].fillna(0)

# Get one known anomalous user
anom_user = df[df['is_anomalous']==1]['user_id'].value_counts().index[0]
anom_df   = df[df['user_id']==anom_user].reset_index(drop=True)
print(f"\nAnomалous user: {anom_user} ({len(anom_df)} events)")
print(f"Anomaly type: {anom_df['anomaly_type'].value_counts().index[0]}")

X = anom_df[FEATURE_COLS].values.astype(np.float32)
y = anom_df['is_anomalous'].values

print(f"\nMSE per sequence for this user:")
for i in range(min(len(anom_df) - SEQ_LEN + 1, 15)):
    seq   = X[i:i+SEQ_LEN]
    flat  = scaler.transform(seq)
    seq_s = flat.reshape(1, SEQ_LEN, INPUT_DIM)
    t     = torch.tensor(seq_s.astype(np.float32))
    with torch.no_grad():
        recon = model(t)
        mse   = float(((recon - t)**2).mean().item())
    label = y[i+SEQ_LEN-1]
    score = min(mse / threshold, 1.0)
    print(f"  seq[{i:2d}] mse={mse:.4f} score={score:.4f} "
          f"label={label} flagged={mse>=threshold}")