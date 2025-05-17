from airflow import DAG
from airflow.operators.python import PythonOperator
from pyspark.sql import SparkSession
from airflow.providers.elasticsearch.hooks.elasticsearch import ElasticsearchHook
from airflow.providers.elasticsearch.hooks.elasticsearch import ElasticsearchPythonHook
from elasticsearch import Elasticsearch
import os
import pandas as pd
from datetime import datetime
import json
"""
def spark_processing():
    spark = SparkSession.builder \
        .appName("AirflowSpark") \
        .getOrCreate()

    # Load the CSV file into a Spark DataFrame
    df = spark.read.csv("/opt/airflow/data/data.csv", header=True, inferSchema=True)
    
    # Perform aggregation (e.g., sum Total_Price by Category)
    aggregated_df = df.groupBy("Category").sum("Total_Price").withColumnRenamed("sum(Total_Price)", "total_price")
    
    # Convert the aggregated DataFrame to JSON for Elasticsearch
    json_data = [row.asDict() for row in aggregated_df.collect()]
    
    # Stop the Spark session
    spark.stop()
    
    # Return the JSON data to be indexed in Elasticsearch
    return json_data

"""

def get_csv_size():
    # Path to the CSV file
    csv_file_path = "/opt/airflow/data/data.csv"
    
    # Get the file size in bytes
    file_size_bytes = os.path.getsize(csv_file_path)
    
    # Optionally, read the CSV file to get the number of rows and columns
    df = pd.read_csv(csv_file_path)
    num_rows = len(df)
    num_columns = len(df.columns)
    
    # Prepare the data to be sent to Elasticsearch
    size_info = {
        "file_name": os.path.basename(csv_file_path),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": file_size_bytes / (1024 * 1024),  # Convert bytes to MB
        "num_rows": num_rows,
        "num_columns": num_columns,
        "timestamp": datetime.utcnow().isoformat()  # Add a timestamp
    }
    
    return size_info


def save_to_es(**kwargs):
    ti = kwargs['ti']
    size_info = ti.xcom_pull(task_ids='get_csv_size_task')

    if not size_info:
        print("No size information received. Skipping Elasticsearch indexing.")
        return

    # Add an index to each key
    indexed_size_info = {f"{i}_{key}": value for i, (key, value) in enumerate(size_info.items())}

    # Directly initialize Elasticsearch client
    es_client = Elasticsearch(["http://elasticsearch:9200"])  # Ensure this matches your setup

    try:
        es_client.index(index='csv_size_info', document=indexed_size_info)  # Use `document` for Elasticsearch 7+
        print(f"Successfully indexed size information: {indexed_size_info}")
    except Exception as e:
        print(f"Failed to index size information. Error: {e}")


with DAG(
    'csv_to_spark_es_pipeline',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:
    
    """
    # Task to run Spark processing
    spark_task = PythonOperator(
        task_id='spark_task',
        python_callable=spark_processing
    )"""
    # Task to get CSV size information
    get_csv_size_task = PythonOperator(
        task_id='get_csv_size_task',
        python_callable=get_csv_size
    )
    
    # Task to save data to Elasticsearch
    es_task = PythonOperator(
        task_id='es_task',
        python_callable=save_to_es,
        provide_context=True  # Pass the context to the task
    )
    
    # Set task dependencies
    #spark_task >> es_task
    get_csv_size_task >> es_task
