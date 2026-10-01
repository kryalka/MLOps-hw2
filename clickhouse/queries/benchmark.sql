SELECT
    table,
    sum(rows) AS total_rows,
    count() AS active_parts,
    sum(data_compressed_bytes) AS compressed_bytes,
    sum(data_uncompressed_bytes) AS uncompressed_bytes,
    sum(bytes_on_disk) AS bytes_on_disk
FROM system.parts
WHERE database = 'fraud'
    AND active = 1
    AND table IN (
        'transactions_base',
        'transactions_optimized',
        'max_transaction_by_state'
    )
GROUP BY table
ORDER BY table;
