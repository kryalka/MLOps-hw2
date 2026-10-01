import csv
import io
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

EXPECTED_ROWS = 262144
EXPECTED_STATES = 51
TIMEOUT = 180
OUTPUT_FILE = "results/max_transaction.csv"
QUERIES = [
    ("transactions_base", "max_transaction.sql"),
    ("transactions_optimized", "max_transaction_optimized.sql"),
    ("max_transaction_by_state", "max_transaction_aggregate.sql"),
]


def query(sql, output_format="CSVWithNames", query_id=""):
    params = {"user": "hw2", "password": "hw2_password", "default_format": output_format}
    if query_id:
        params["query_id"] = query_id
    request = Request("http://localhost:8123/?" + urlencode(params), data=sql.encode())
    with urlopen(request, timeout=120) as response:
        return response.read().decode()


def check_data():
    deadline = time.monotonic() + TIMEOUT
    while True:
        ready = True
        for table in ["transactions_base", "transactions_optimized"]:
            sql = f"SELECT count(), uniqExact(transaction_id), uniqExact(us_state) FROM fraud.{table}"
            count, unique_ids, states = map(int, query(sql, "TabSeparated").split())
            if count > EXPECTED_ROWS or count != unique_ids:
                raise ValueError(f"{table}: лишние строки или повторяющиеся ID")
            if count < EXPECTED_ROWS:
                ready = False
            elif states != EXPECTED_STATES:
                raise ValueError(f"{table}: ожидалось {EXPECTED_STATES} штатов, получено {states}")
        if ready:
            break
        if time.monotonic() >= deadline:
            raise TimeoutError("Не все транзакции загрузились")
        print("Ожидание загрузки...", flush=True)
        time.sleep(1)

    while True:
        results = []
        for table, filename in QUERIES:
            sql = Path("clickhouse/queries", filename).read_text().strip().rstrip(";")
            results.append(query(sql))
        if results[0] == results[1] == results[2]:
            rows = list(csv.DictReader(io.StringIO(results[2])))
            if len(rows) != EXPECTED_STATES:
                raise ValueError("В результате должно быть по одной строке на штат")
            return results[2]
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Результаты трех SQL-запросов не совпали")
        print("Ожидание агрегированной таблицы...", flush=True)
        time.sleep(min(1, remaining))


def main():
    result = check_data()
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_FILE).write_text(result, encoding="utf-8")
    print("Данные проверены. Результат:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
