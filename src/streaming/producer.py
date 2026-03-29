import pandas as pd
import json
import time
from kafka import KafkaProducer

TOPIC = "forex_events"

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

def stream_data():
    df = pd.read_csv("data/processed/features.csv")
    df = df.sort_values("timestamp").reset_index(drop=True)

    for _, row in df.iterrows():
        event = row.to_dict()

        producer.send(TOPIC, value=event)

        print(f"Sent user: {event.get('user_id')}")
        time.sleep(0.05)

if __name__ == "__main__":
    stream_data()