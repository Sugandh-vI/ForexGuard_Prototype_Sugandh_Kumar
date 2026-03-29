import pandas as pd
import time
import yaml
from kafka import KafkaProducer
import json
from src.utils.logger import get_logger

logger = get_logger(__name__)

with open("configs/config.yaml", "r") as f:
    config = yaml.safe_load(f)

BATCH_SIZE = config["streaming"]["batch_size"]
DELAY      = config["streaming"]["delay_seconds"]

TOPIC = "forex_events"

# ---------------- PRODUCER ----------------
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# ---------------- STREAMING ----------------
def stream_events(csv_path: str,
                  max_batches: int = 20,
                  verbose: bool = True):

    df = pd.read_csv(csv_path)
    df = df.sort_values("timestamp").reset_index(drop=True)

    batch_count = 0

    for start in range(0, len(df), BATCH_SIZE):

        if batch_count >= max_batches:
            break

        batch = df.iloc[start: start + BATCH_SIZE]

        for _, row in batch.iterrows():
            event = row.to_dict()

            producer.send(TOPIC, value=event)

        batch_count += 1

        if verbose:
            print(f"📦 Sent Batch {batch_count} ({len(batch)} events)")

        time.sleep(DELAY)

    print("✅ Streaming complete")


# ---------------- RUN ----------------
def run_streaming_pipeline():
    return stream_events(config["data"]["processed_path"])


if __name__ == "__main__":
    run_streaming_pipeline()


# import pandas as pd
# import numpy as np   # 🔥 ADD THIS
# import time
# import yaml
# import requests
# from src.utils.logger import get_logger

# logger = get_logger(__name__)

# with open("configs/config.yaml", "r") as f:
#     config = yaml.safe_load(f)

# BATCH_SIZE = config["streaming"]["batch_size"]
# DELAY      = config["streaming"]["delay_seconds"]

# API_URL = "http://127.0.0.1:8000/score"


# # ---------------- CLEAN EVENT ----------------
# def clean_event(event: dict):
#     clean = {}

#     for k, v in event.items():
#         try:
#             if pd.isna(v) or v is None:
#                 clean[k] = 0.0
#             elif isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
#                 clean[k] = 0.0
#             else:
#                 clean[k] = float(v) if isinstance(v, (int, float)) else v
#         except:
#             clean[k] = 0.0

#     return clean


# # ---------------- API CALL ----------------
# def call_api(event: dict):
#     try:
#         response = requests.post(API_URL, json={"data": event})

#         if response.status_code != 200:
#             return {"error": f"HTTP {response.status_code}"}

#         data = response.json()

#         if not isinstance(data, dict):
#             return {"error": "Invalid JSON response"}

#         return data

#     except Exception as e:
#         return {"error": str(e)}


# # ---------------- STREAMING ----------------
# def stream_events(csv_path: str,
#                   max_batches: int = 20,
#                   verbose: bool = True):

#     df = pd.read_csv(csv_path)

#     # 🔥 REAL STREAM ORDER
#     df = df.sort_values("timestamp").reset_index(drop=True)

#     results = []
#     anomalies = []
#     batch_count = 0

#     for start in range(0, len(df), BATCH_SIZE):

#         if batch_count >= max_batches:
#             break

#         batch = df.iloc[start: start + BATCH_SIZE]
#         batch_results = []

#         for _, row in batch.iterrows():

#             # 🔥 CRITICAL FIX
#             event = clean_event(row.to_dict())

#             result = call_api(event)

#             if "error" in result:
#                 print("API ERROR:", result["error"])
#                 continue

#             if "is_anomaly" not in result:
#                 print("INVALID RESPONSE:", result)
#                 continue

#             results.append(result)
#             batch_results.append(result)

#             if result["is_anomaly"]:
#                 anomalies.append(result)

#         batch_count += 1

#         if verbose:
#             flagged = [r for r in batch_results if r["is_anomaly"]]

#             print(f"\n── Batch {batch_count:3d} │ Flagged: {len(flagged)}/{len(batch_results)}")

#             for r in sorted(flagged, key=lambda x: x["anomaly_score"], reverse=True)[:3]:
#                 print(f"   🚨 {r['severity']} │ user={r['user_id']} "
#                       f"│ type={r['event_type']:12s} "
#                       f"│ score={r['anomaly_score']:.3f}")

#                 for reason in r["reasons"]:
#                     print(f"      → {reason}")

#         time.sleep(DELAY)

#     # ---------------- SUMMARY ----------------
#     print(f"\n{'='*60}")
#     print("  STREAMING SUMMARY")
#     print(f"{'='*60}")
#     print(f"  Batches processed : {batch_count}")
#     print(f"  Events scored     : {len(results)}")
#     print(f"  Anomalies flagged : {len(anomalies)}")
#     print(f"  Detection type    : Behavioral (unsupervised)")
#     print(f"  Anomaly rate      : {len(anomalies)/max(len(results),1)*100:.1f}%")

#     return results, anomalies


# # ---------------- RUN ----------------
# def run_streaming_pipeline():
#     return stream_events(config["data"]["processed_path"])


# if __name__ == "__main__":
#     run_streaming_pipeline()