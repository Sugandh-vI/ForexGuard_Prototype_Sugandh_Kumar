import pandas as pd
import numpy as np
import torch
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from src.models.lstm_autoencoder import FEATURE_COLS, INPUT_DIM, LSTMAutoencoder
import yaml

with open("configs/config.yaml") as f:
    config = yaml.safe_load(f)

CFG     = config["model"]["lstm_autoencoder"]
SEQ_LEN = CFG["sequence_length"]

model = LSTMAutoencoder(INPUT_DIM, CFG["hidden_dim"], CFG["latent_dim"])
model.load_state_dict(torch.load("saved_models/lstm_autoencoder.pt", map_location="cpu"))
model.eval()
scaler = joblib.load("saved_models/lstm_scaler.pkl")

df = pd.read_csv('data/processed/features.csv').sort_values('timestamp')
df[FEATURE_COLS] = df[FEATURE_COLS].fillna(0)

# ── Step 1: Split USERS into train/val/test ───────────────────────────────────
# Split at user level — not event level — to prevent leakage
# A user's events should never span both train and val
normal_users = df[df['is_anomalous']==0]['user_id'].unique()
anom_users   = df[df['is_anomalous']==1]['user_id'].unique()

# 70% train / 15% val / 15% test (normal users only for threshold setting)
train_users, temp_users = train_test_split(normal_users, test_size=0.30, random_state=42)
val_users,   test_users = train_test_split(temp_users,   test_size=0.50, random_state=42)

print(f"User split:")
print(f"  Train (normal): {len(train_users)}")
print(f"  Val   (normal): {len(val_users)}")
print(f"  Test  (normal): {len(test_users)}")
print(f"  Anomalous     : {len(anom_users)}")

# ── Step 2: Compute MSE per sequence ─────────────────────────────────────────
def get_mse_for_users(user_list, label_override=None):
    mse_list, label_list = [], []
    subset = df[df['user_id'].isin(user_list)]
    for uid, group in subset.groupby('user_id'):
        group = group.reset_index(drop=True)
        X = group[FEATURE_COLS].values.astype(np.float32)
        y = group['is_anomalous'].values
        for i in range(len(group) - SEQ_LEN + 1):
            seq   = X[i:i+SEQ_LEN]
            label = label_override if label_override is not None else y[i+SEQ_LEN-1]
            flat  = scaler.transform(seq)
            seq_s = flat.reshape(1, SEQ_LEN, INPUT_DIM)
            t     = torch.tensor(seq_s.astype(np.float32))
            with torch.no_grad():
                recon = model(t)
                mse   = float(((recon - t)**2).mean().item())
            mse_list.append(mse)
            label_list.append(label)
    return np.array(mse_list), np.array(label_list)

print("\nComputing MSE for validation users (threshold setting)...")
val_mse, val_labels = get_mse_for_users(val_users)

print("Computing MSE for test users + anomalous users (final eval)...")
test_mse,  test_labels  = get_mse_for_users(test_users)
anom_mse,  anom_labels  = get_mse_for_users(anom_users)

# Combine test normal + all anomalous for final evaluation
eval_mse    = np.concatenate([test_mse, anom_mse])
eval_labels = np.concatenate([test_labels, anom_labels])

# ── Step 3: Set threshold on VAL set only ────────────────────────────────────
# p95 of validation normal MSE — anything above this is anomalous
threshold = np.percentile(val_mse, 95)
print(f"\nVal MSE   — mean={val_mse.mean():.4f} p90={np.percentile(val_mse,90):.4f} p95={threshold:.4f}")
print(f"Anom MSE  — mean={anom_mse.mean():.4f}")
print(f"\nNew threshold (p95 of val normal): {threshold:.6f}")

# ── Step 4: Evaluate on TEST set (never seen during threshold setting) ────────
preds = (eval_mse >= threshold).astype(int)

print("\n" + "="*55)
print("  FINAL EVALUATION (held-out test set)")
print("="*55)
try:
    auc = roc_auc_score(eval_labels, eval_mse)
    print(f"  ROC-AUC: {auc:.4f}")
except:
    pass
print(classification_report(eval_labels, preds,
      target_names=["Normal","Anomaly"], zero_division=0))

# ── Step 5: Save proper threshold ────────────────────────────────────────────
joblib.dump(threshold, "saved_models/lstm_threshold.pkl")
print(f"Threshold {threshold:.6f} saved to saved_models/lstm_threshold.pkl")