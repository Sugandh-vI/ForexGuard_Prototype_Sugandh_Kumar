# 🚀 ForexGuard Prototype — Real-Time Anomaly Detection Engine

## 📌 Overview

ForexGuard is a production-grade real-time anomaly detection system designed to identify suspicious trader behavior in a forex brokerage environment.

The system processes user activity across:

* Client Portal (logins, deposits, withdrawals, sessions)
* Trading Systems (trade volume, PnL, margin usage, patterns)

It uses **unsupervised machine learning + streaming architecture** to generate **explainable risk alerts** for compliance teams.

---

## 🎯 Objective

* Detect anomalous users using **unsupervised learning**
* Process events in **real-time (Kafka / Redpanda)**
* Provide **explainable anomaly scores**
* Generate **human-readable alerts**

---

## 🏗️ System Architecture

```
Synthetic Data → Feature Engineering → Producer → Kafka → Consumer → LSTM Scorer → Alerts
```

---

## ⚙️ Pipeline (End-to-End)

Controlled via:

```bash
python main.py --step <data|features|train|stream|serve>
```

### Steps:

* `data` → Generate synthetic dataset (~50,000 events)
* `features` → Feature engineering pipeline
* `train` → Train Isolation Forest + LSTM
* `stream` → Simulated real-time pipeline
* `serve` → FastAPI deployment

---

## 📊 Feature Engineering

Includes ~46 engineered features :

### Statistical

* Rolling mean/std (5, 10, 30 windows)
* Z-score normalization

### Behavioral

* Session duration
* Click rate
* Failed login attempts

### Temporal

* Time since last event/login/deposit
* Burst activity detection

### Trading

* Trade volume vs baseline
* PnL patterns
* Margin usage

### Network / Identity

* Unique IPs, devices, countries

---

## 🧠 Models

### 1️⃣ Isolation Forest (Baseline)

* ROC-AUC: **0.517**
* Avg Precision: **0.131**
* Weak anomaly detection (expected for complex sequences)

---

### 2️⃣ LSTM Autoencoder (Advanced)

* Sequence length: 10
* Input features: 46
* Hidden dim: 64 | Latent: 32

#### Results:

* ROC-AUC: **0.702**
* Avg Precision: **0.408**
* Precision (Anomaly): **0.82**
* Recall (Anomaly): **0.31**

👉 Strong improvement over baseline

---

## 🔍 Model Design

### LSTM Autoencoder

* Encoder → compresses sequence → latent space
* Decoder → reconstructs sequence
* **Anomaly = high reconstruction error**

### Key Design Choices:

* Train ONLY on normal behavior
* Threshold = **98th percentile**
* Stateful per-user sequence buffering

---

## ⚡ Real-Time Streaming

Implemented using Kafka-compatible Redpanda:

### Producer

* Reads engineered dataset
* Streams events to topic `forex_events`

### Consumer

* Consumes events
* Uses `ForexGuardScorer` 
* Maintains per-user buffers
* Scores sequences in real-time

### Output Example:

```
🚨 ANOMALY DETECTED
User: USER_0202
Score: 4.0912
Severity: HIGH
→ Unusual transaction amount
```

---

## 🧠 Scoring Engine

Key features:

* Stateful sequence tracking (deque buffer)
* Dynamic anomaly scoring
* Severity classification:

  * LOW / MEDIUM / HIGH / CRITICAL
* Top contributing features
* Human-readable explanations

---

## 🌐 API Layer

FastAPI endpoint:

```
POST /score
```

Returns:

* anomaly_score
* is_anomaly
* severity
* reasons
* top_features
* verdict

---

## 📦 Dataset

* 50,000 synthetic events
* 500 users
* 5% anomaly rate

Includes:

* Login behavior
* Trading activity
* Deposits & withdrawals
* Session patterns

---

## 🚨 Anomaly Types Captured

✔ Login anomalies (failed attempts, unusual timing)
✔ Financial anomalies (withdrawal spikes, abuse patterns)
✔ Trading anomalies (volume spikes, abnormal PnL)
✔ Behavioral anomalies (burst activity, session anomalies)

---

## ⚙️ Setup Instructions

### 1. Clone

```bash
git clone https://github.com/Sugandh-vI/ForexGuard_Prototype_Sugandh_Kumar.git
cd ForexGuard_Prototype_Sugandh_Kumar
```

---

### 2. Install

```bash
uv sync
```

---

### 3. Start Kafka (Redpanda)

```bash
docker run -d --name redpanda -p 9092:9092 docker.redpanda.com/redpandadata/redpanda:latest redpanda start --overprovisioned --smp 1 --memory 1G --reserve-memory 0M --node-id 0 --check=false
```

---

### 4. Create Topic

```bash
docker exec -it redpanda rpk topic create forex_events
```

---

### 5. Run Consumer

```bash
uv run python -m src.streaming.consumer
```

---

### 6. Run Producer

```bash
uv run python -m src.streaming.producer
```

---

### 7. Run API

```bash
python main.py --step serve
```

---

## 🧠 Assumptions

* Synthetic data approximates real-world patterns
* User behavior is sequential and predictable
* Anomalies deviate significantly from learned patterns

---

## ⚠️ Limitations

* Synthetic dataset (not real-world)
* Single-node Kafka
* Limited hyperparameter tuning
* No UI/dashboard

---

## 🚀 Future Improvements

* Streamlit dashboard
* Cloud deployment (AWS / Render)
* LLM-based risk summaries
* Graph-based fraud detection
* Multi-user scaling

---

## 🏁 Conclusion

ForexGuard demonstrates a **production-grade ML system** integrating:

* Real-time streaming
* Sequential anomaly detection (LSTM)
* Explainable AI
* Scalable architecture

This project goes beyond modeling and showcases **end-to-end system design for fraud detection**.

---

## 👨‍💻 Author

Sugandh Kumar
