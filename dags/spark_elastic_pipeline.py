from airflow import DAG
from airflow.operators.python import PythonOperator
from pyspark.sql import SparkSession
from elasticsearch import Elasticsearch
from datetime import datetime
from pyspark.sql.functions import sum, col

from pyspark.sql import SparkSession
from pyspark.sql.functions import sum, col, when, count

def spark_processing():
    spark = SparkSession.builder \
        .appName("AirflowSparkCSVProcessing").config("spark.driver.memory", "4g").config("spark.executor.memory", "4g").config("spark.memory.fraction", "0.8").config("spark.memory.storageFraction", "0.5").config("spark.jars.packages", "org.elasticsearch:elasticsearch-spark-30_2.12:8.12.0").getOrCreate()
    
    # Load all CSV files into a DataFrame
    df = spark.read.csv("/opt/airflow/data/generated_data_*.csv", header=True, inferSchema=True, sep="|")
    
    # Perform some transformations and aggregations
    result_df = df.withColumn("Total_Active_Sessions", col("afActiveSessions") + col("amfActiveSessions") + col("fixedActiveSessions") + col("mobileActiveSessions") + col("sdActiveSessions") + col("smfActiveSessions") + col("smpActiveGlobalSessions")) \
        .withColumn("High_Signalling_Sessions", when(col("afSignallingActiveSessions") > 5, 1).otherwise(0)) \
        .groupBy("TimeStamp") \
        .agg(
            sum("Total_Active_Sessions").alias("Total_Active_Sessions_Sum"),
            sum("High_Signalling_Sessions").alias("High_Signalling_Sessions_Count"),
            sum("gxCcasInitSuccess@SO1GG2").alias("Total_gxCcasInitSuccess_SO1GG2"),
            sum("gxCcasTerminateSuccess@TN1GG2").alias("Total_gxCcasTerminateSuccess_TN1GG2"),
            sum("gxRaasSuccess@TN2GG2").alias("Total_gxRaasSuccess_TN2GG2"),
            count("*").alias("Total_Records")
        ) \
        .orderBy("TimeStamp")
    result_df.write \
        .format("org.elasticsearch.spark.sql") \
        .option("es.nodes", "elasticsearch").option("es.port", "9200").option("es.resource", "spark_data").mode("append").save()
    
    # Stop the Spark session
    spark.stop()
    
    # Return a success message (small data for XCom)
    return "Data successfully written to Elasticsearch"

# The rest of your DAG and task definitions remain the same
def save_to_es(**kwargs):
    ti = kwargs['ti']
    data = ti.xcom_pull(task_ids='spark_task')
    
    # Initialize Elasticsearch client directly
    es = Elasticsearch("http://elasticsearch:9200")
    
    # Index each document in Elasticsearch
    for doc in data:
        es.index(
            index='spark_data',    # Elasticsearch index name
            body=doc              # JSON document
        )

# Define the DAG
with DAG(
    'POC_orange',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:
    
    # Task to run Spark processing
    spark_task = PythonOperator(
        task_id='spark_task',
        python_callable=spark_processing
    )
    
    # Task to save data to Elasticsearch
    es_task = PythonOperator(
        task_id='es_task',
        python_callable=save_to_es,
        provide_context=True  # Make sure we pass the context to the task
    )
    
    """# Set task dependencies
    spark_task >> es_task"""


    spark_task