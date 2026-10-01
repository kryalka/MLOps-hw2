CREATE MATERIALIZED VIEW IF NOT EXISTS fraud.mv_max_transaction
TO fraud.max_transaction_by_state
AS
SELECT
    toString(us_state) AS us_state,

    argMaxState(
        tuple(toString(cat_id), amount),
        tuple(amount, transaction_id)
    ) AS max_transaction_state

FROM fraud.transactions_optimized
GROUP BY us_state;

CREATE MATERIALIZED VIEW IF NOT EXISTS fraud.mv_transactions_optimized
TO fraud.transactions_optimized
AS
SELECT *
FROM fraud.transactions_base;

CREATE MATERIALIZED VIEW IF NOT EXISTS fraud.mv_transactions_base
TO fraud.transactions_base
AS
SELECT *
FROM fraud.transactions_kafka;
