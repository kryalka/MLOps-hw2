import json
import statistics
import time
from pathlib import Path
from export_results import QUERIES, check_data, query

RUNS = 9
WARMUP = 2
OUTPUT_FILE = "results/benchmark.json"
SETTINGS = (
    "max_threads=2, optimize_aggregation_in_order=1, use_query_cache=0, "
    "log_queries=1, log_queries_probability=1, log_queries_min_query_duration_ms=0"
)


def main():
    if RUNS < 3 or WARMUP < 1:
        raise ValueError("Нужно хотя бы 3 замера и 1 прогрев")
    check_data()
    for table, filename in QUERIES:
        query(f"OPTIMIZE TABLE fraud.{table} FINAL")

    report = {
        "clickhouse_version": query("SELECT version()", "TabSeparated").strip(),
        "runs": RUNS, "warmup": WARMUP, "settings": SETTINGS, "queries": {},
    }
    for table, filename in QUERIES:
        sql = Path("clickhouse/queries", filename).read_text().strip().rstrip(";")
        sql += "\nSETTINGS " + SETTINGS
        for i in range(WARMUP):
            query(sql, "Null")

        prefix = f"hw2-{time.time_ns()}-{table}"
        for i in range(RUNS):
            query(sql, "Null", f"{prefix}-{i}")
        query("SYSTEM FLUSH LOGS")
        log = query(
            "SELECT query_id, query_duration_ms, read_rows, read_bytes, memory_usage "
            "FROM system.query_log WHERE type = 'QueryFinish' "
            f"AND startsWith(query_id, '{prefix}-') ORDER BY query_id",
            "JSONEachRow",
        )
        samples = []
        for line in log.splitlines():
            samples.append(json.loads(line))
        if len(samples) != RUNS:
            raise RuntimeError("В query_log не хватает замеров")
        times = [sample["query_duration_ms"] for sample in samples]
        report["queries"][table] = {
            "median_ms": statistics.median(times),
            "min_ms": min(times), "max_ms": max(times), "samples": samples,
        }
        print(table, "медиана:", statistics.median(times), "мс", flush=True)

    sizes = query(Path("clickhouse/queries/benchmark.sql").read_text(), "JSONEachRow")
    report["storage"] = []
    for line in sizes.splitlines():
        report["storage"].append(json.loads(line))
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_FILE).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Замеры сохранены:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
