from kafka import KafkaConsumer
import json
from src.models.scorer import ForexGuardScorer

TOPIC = "forex_events"

# ---- INIT SCORER ----
scorer = ForexGuardScorer()

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)

def consume():
    print("🚀 Consumer started...")

    total = 0
    anomalies = 0

    for message in consumer:
        event = message.value

        result = scorer.score(event)

        total += 1

        if result["is_anomaly"]:
            anomalies += 1

            print("\n🚨 ANOMALY DETECTED")
            print(f"User: {result['user_id']}")
            print(f"Score: {result['anomaly_score']:.4f}")
            print(f"Severity: {result['severity']}")

            for r in result["reasons"]:
                print(f"  → {r}")

        if total % 100 == 0:
            print(f"\n📊 Processed: {total} | Anomalies: {anomalies}")

if __name__ == "__main__":
    consume()