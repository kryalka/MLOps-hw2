import argparse
import csv
import json
import os
from pathlib import Path
from confluent_kafka import Producer

COLUMNS = [
    "transaction_time", "merch", "cat_id", "amount", "name_1", "name_2",
    "gender", "street", "one_city", "us_state", "post_code", "lat", "lon",
    "population_city", "jobs", "merchant_lat", "merchant_lon"
]

parser = argparse.ArgumentParser()
parser.add_argument("--file", default="data/test.csv")
parser.add_argument("--limit", type=int, default=0)
args = parser.parse_args()
if args.limit < 0:
    parser.error("--limit must be non-negative")

errors = []


def delivery_report(error, message):
    if error is not None:
        errors.append(str(error))


producer = Producer({
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9096"),
    "enable.idempotence": True,
    "acks": "all",
})
path = Path(args.file)
sent = 0

with path.open(encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)
    for column in COLUMNS:
        if column not in (reader.fieldnames or []):
            raise ValueError(f"Missing column: {column}")

    for index, row in enumerate(reader):
        if args.limit and index >= args.limit:
            break
        transaction = {column: row[column] for column in COLUMNS}
        transaction["transaction_id"] = f"{path.stem}-{index}"
        if len(transaction["transaction_time"]) == 16:
            transaction["transaction_time"] += ":00"
        for column in ["lat", "lon", "merchant_lat", "merchant_lon"]:
            transaction[column] = float(transaction[column])
        transaction["population_city"] = int(transaction["population_city"])
        transaction["target"] = None
        if row.get("target"):
            transaction["target"] = int(row["target"])

        while True:
            try:
                producer.produce(
                    "transactions", key=transaction["transaction_id"],
                    value=json.dumps(transaction).encode(), on_delivery=delivery_report,
                )
                break
            except BufferError:
                producer.poll(1)
        producer.poll(0)
        sent += 1

remaining = producer.flush(60)
if remaining or errors:
    raise RuntimeError(f"Unsent: {remaining}, errors: {errors}")
print(f"Successfully delivered: {sent}")
