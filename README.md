# MLOps-hw2

Поиск категории самой большой отдельной транзакции в каждом штате.
При равных суммах выбирается лексикографически наибольший `transaction_id`.

`CSV → Python producer → Kafka → ClickHouse (Materialized Views) → CSV`

## Запуск

Нужны запущенный Docker, Compose 2.20+, Python 3.9+ и свободные порты 9096 и 8123.
Скачайте `test.csv` с [Kaggle](https://www.kaggle.com/t/1918f3f6435300327d38d6c596f97394) и положите в `data/`. Ниже инструкция для работы с файлом `test.csv`!
Все команды выполняются из корня проекта.

```bash
docker compose build producer
docker compose up -d --wait --wait-timeout 180
docker compose run --rm producer --file data/test.csv
python3 scripts/export_results.py
python3 scripts/benchmark.py
```

Топик Kafka и таблицы создаются автоматически. DDL находится в `clickhouse/init/`, запросы — в `clickhouse/queries/`.
Экспорт ждет загрузку до 180 секунд, проверяет количество строк, уникальность ID, число штатов и совпадение трех SQL-ответов.
Результат из ClickHouse: `results/max_transaction.csv`, столбцы `us_state,cat_id,max_amount`.

Выполнить базовый SQL отдельно:

```bash
docker compose exec -T clickhouse clickhouse-client --user hw2 --password hw2_password < clickhouse/queries/max_transaction.sql
```

## Оптимизация и замеры

Базовая таблица — MergeTree без сортировки. В оптимизированной используются `LowCardinality` для штата, категории и пола и `ORDER BY (us_state, amount)`.
Таблица на AggregatingMergeTree рассчитывает максимумы при загрузке.

Замеры ClickHouse 25.8.33.6: два прогрева и девять запусков после `OPTIMIZE FINAL`, два потока, кеш ответов выключен, `FORMAT Null`.
Время и чтение берутся из `system.query_log`, размеры — из активных `system.parts`. Все замеры сохранены в `results/benchmark.json`.

| Вариант | Медиана, мс | Прочитано строк | Прочитано байт | На диске, байт |
| --- | ---: | ---: | ---: | ---: |
| Базовый | 41 | 262144 | 14444422 | 20508039 |
| Оптимизированный | 15 | 262144 | 7492145 | 16921005 |
| Таблица с максимумами по штатам | 1 | 51 | 7446 | 1441 |

Полная оптимизированная таблица быстрее в **2,73 раза** и занимает на **17,5% меньше места**.
Отдельная таблица хранит заранее рассчитанные максимумы по штатам.

Для другого CSV измените `EXPECTED_ROWS` и `EXPECTED_STATES` в `scripts/export_results.py`; число запусков задается через `RUNS` и `WARMUP` в `scripts/benchmark.py`.

## Остановка и повторный запуск

`docker compose down` сохраняет данные. Для продолжения выполните команду `up` из блока запуска и экспорт, без повторной отправки CSV.
Повторная отправка CSV добавит дубли. Для нового теста удалите данные контейнеров и повторите блок запуска:

```bash
docker compose down --volumes --remove-orphans
```

`backfill_aggregate.sql` нужен только для восстановления пустой агрегированной таблицы; при штатной загрузке его запускать не нужно.
Проверены полный цикл загрузки, правильность SQL, повторный запуск и сохранение данных. Итоговый CSV совпадает между чистыми запусками.
