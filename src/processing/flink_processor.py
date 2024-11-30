from pyflink.datastream import StreamExecutionEnvironment, TimeCharacteristic
from pyflink.table import StreamTableEnvironment, DataTypes
from pyflink.table.udf import udf
from pyflink.common.serialization import SimpleStringSchema
import json
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StockProcessor:
    def __init__(self):
        # Create execution environment
        self.env = StreamExecutionEnvironment.get_execution_environment()
        self.env.set_parallelism(1)
        self.env.set_stream_time_characteristic(TimeCharacteristic.ProcessingTime)
        
        # Create table environment
        self.t_env = StreamTableEnvironment.create(self.env)

    def add_kafka_connector(self):
        # Download Kafka connector JAR if not exists
        kafka_jar = "flink-sql-connector-kafka_2.12-1.17.1.jar"
        if not os.path.exists(kafka_jar):
            logger.info("Downloading Kafka connector...")
            os.system(
                f"wget https://repo.maven.apache.org/maven2/org/apache/flink/"
                f"flink-sql-connector-kafka_2.12/1.17.1/{kafka_jar}"
            )
        
        self.env.add_jars(f"file://{os.path.abspath(kafka_jar)}")

    def create_kafka_source_table(self):
        # Create source table from Kafka
        source_ddl = """
            CREATE TABLE stock_data (
                symbol STRING,
                name STRING,
                price DOUBLE,
                change STRING,
                volume BIGINT,
                timestamp STRING,
                proctime AS PROCTIME()
            ) WITH (
                'connector' = 'kafka',
                'topic' = 'stock_data',
                'properties.bootstrap.servers' = 'localhost:9092',
                'properties.group.id' = 'stock_processor',
                'format' = 'json',
                'scan.startup.mode' = 'latest-offset'
            )
        """
        self.t_env.execute_sql(source_ddl)

    def create_kafka_sink_table(self):
        # Create sink table to Kafka
        sink_ddl = """
            CREATE TABLE processed_stock_data (
                symbol STRING,
                name STRING,
                price DOUBLE,
                price_change DOUBLE,
                volume BIGINT,
                timestamp STRING
            ) WITH (
                'connector' = 'kafka',
                'topic' = 'processed_stock_data',
                'properties.bootstrap.servers' = 'localhost:9092',
                'format' = 'json'
            )
        """
        self.t_env.execute_sql(sink_ddl)

    @udf(result_type=DataTypes.DOUBLE())
    def extract_price_change(change_str):
        try:
            return float(change_str.replace('%', '').strip())
        except:
            return 0.0

    def process_data(self):
        # Register UDF
        self.t_env.create_temporary_function(
            'extract_price_change',
            udf(self.extract_price_change, DataTypes.STRING(), DataTypes.DOUBLE())
        )

        # Process data with SQL
        query = """
            INSERT INTO processed_stock_data
            SELECT
                symbol,
                name,
                price,
                extract_price_change(change) as price_change,
                volume,
                timestamp
            FROM stock_data
        """
        self.t_env.execute_sql(query)

    def run(self):
        try:
            logger.info("Starting Flink Stock Processor...")
            self.add_kafka_connector()
            self.create_kafka_source_table()
            self.create_kafka_sink_table()
            self.process_data()
        except Exception as e:
            logger.error(f"Error in Flink processing: {e}")
            raise

if __name__ == "__main__":
    processor = StockProcessor()
    processor.run()
