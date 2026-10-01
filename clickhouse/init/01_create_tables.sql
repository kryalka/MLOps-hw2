CREATE DATABASE IF NOT EXISTS fraud;


CREATE TABLE IF NOT EXISTS fraud.transactions_kafka
(
    transaction_id String,
    transaction_time DateTime,
    merch String,
    cat_id String,
    amount Decimal(12, 2),
    name_1 String,
    name_2 String,
    gender String,
    street String,
    one_city String,
    us_state String,
    post_code String,
    lat Float64,
    lon Float64,
    population_city UInt32,
    jobs String,
    merchant_lat Float64,
    merchant_lon Float64,
    target Nullable(UInt8)
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'transactions',
    kafka_group_name = 'clickhouse_transactions',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 1;


CREATE TABLE IF NOT EXISTS fraud.transactions_base
AS fraud.transactions_kafka
ENGINE = MergeTree()
ORDER BY tuple();


CREATE TABLE IF NOT EXISTS fraud.transactions_optimized
(
    transaction_id String,
    transaction_time DateTime,
    merch String,
    cat_id LowCardinality(String),
    amount Decimal(12, 2),
    name_1 String,
    name_2 String,
    gender LowCardinality(String),
    street String,
    one_city String,
    us_state LowCardinality(String),
    post_code String,
    lat Float64,
    lon Float64,
    population_city UInt32,
    jobs String,
    merchant_lat Float64,
    merchant_lon Float64,
    target Nullable(UInt8)
)
ENGINE = MergeTree()
ORDER BY (us_state, amount)
PRIMARY KEY us_state;

CREATE TABLE IF NOT EXISTS fraud.max_transaction_by_state
(
    us_state String,

    max_transaction_state AggregateFunction(
        argMax,
        Tuple(String, Decimal(12, 2)),
        Tuple(Decimal(12, 2), String)
    )
)
ENGINE = AggregatingMergeTree()
ORDER BY us_state;
