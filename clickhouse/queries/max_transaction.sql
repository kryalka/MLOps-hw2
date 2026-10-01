SELECT
    us_state,
    argMax(cat_id, tuple(amount, transaction_id)) AS cat_id,
    max(amount) AS max_amount
FROM fraud.transactions_base
GROUP BY us_state
ORDER BY us_state;
