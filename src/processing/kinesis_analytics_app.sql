-- Create source stream
CREATE OR REPLACE STREAM "SOURCE_SQL_STREAM" (
    symbol VARCHAR(4),
    name VARCHAR(100),
    price DOUBLE,
    change VARCHAR(20),
    volume BIGINT,
    timestamp VARCHAR(30)
);

-- Create output stream for processed data
CREATE OR REPLACE STREAM "DESTINATION_SQL_STREAM" (
    symbol VARCHAR(4),
    name VARCHAR(100),
    avg_price DOUBLE,
    max_price DOUBLE,
    min_price DOUBLE,
    volume_sum BIGINT,
    timestamp VARCHAR(30)
);

-- Calculate real-time analytics
-- This query computes average, max, and min prices over a 5-minute window
CREATE OR REPLACE PUMP "STREAM_PUMP" AS
INSERT INTO "DESTINATION_SQL_STREAM"
SELECT STREAM
    symbol,
    name,
    AVG(price) AS avg_price,
    MAX(price) AS max_price,
    MIN(price) AS min_price,
    SUM(volume) AS volume_sum,
    MAX(timestamp) AS timestamp
FROM "SOURCE_SQL_STREAM"
GROUP BY 
    symbol,
    name,
    FLOOR("SOURCE_SQL_STREAM".ROWTIME TO MINUTE),
    STEP("SOURCE_SQL_STREAM".ROWTIME BY INTERVAL '5' MINUTE);
