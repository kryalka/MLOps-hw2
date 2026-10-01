INSERT INTO fraud.max_transaction_by_state
SELECT
    CAST(t.us_state AS String) AS us_state,
    argMaxState(
        tuple(CAST(t.cat_id AS String), t.amount),
        tuple(t.amount, t.transaction_id)
    ) AS max_transaction_state
FROM fraud.transactions_optimized AS t
GROUP BY t.us_state;