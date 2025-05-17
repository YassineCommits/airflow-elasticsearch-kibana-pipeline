from airflow import DAG
from airflow.operators.python import PythonOperator
from pyspark.sql import SparkSession
from elasticsearch import Elasticsearch
from datetime import datetime
from pyspark.sql.functions import sum, col, when, count
import os
import glob

def spark_processing():
    print("=== Starting Spark CSV Processing DAG ===")
    
    try:
        spark = SparkSession.builder \
            .appName("AirflowSparkCSVSequentialProcessing") \
            .config("spark.driver.memory", "4g") \
            .config("spark.executor.memory", "4g") \
            .config("spark.memory.fraction", "0.8") \
            .config("spark.memory.storageFraction", "0.5") \
            .config("spark.jars.packages", "org.elasticsearch:elasticsearch-spark-30_2.12:8.12.0") \
            .config("spark.driver.maxResultSize", "4g") \
            .getOrCreate()
        
        print("[INFO] Spark session successfully created.")
        
        data_path = "/opt/airflow/data"
        print(f"[INFO] Looking for CSV files in directory: {data_path}")
        files = sorted(glob.glob(os.path.join(data_path, "generated_data_*.csv")))

        if not files:
            print("[WARNING] No CSV files found.")
            return "No files found or processed."

        print(f"[INFO] {len(files)} file(s) found for processing.")
        
        for idx, file in enumerate(files, start=1):
            print(f"[INFO] Processing file {idx}/{len(files)}: {file}")
            
            try:
                df = spark.read.csv(file, header=True, inferSchema=True, sep="|")
                print(f"[INFO] File {file} successfully read with {df.count()} rows.")

                print("[INFO] Applying sampling transformation...")
                df = df.sample(fraction=0.3, seed=42)
                print(f"[INFO] Sampled DataFrame has {df.count()} rows.")

                print("[INFO] Writing to Elasticsearch...")
                df.write \
                    .format("org.elasticsearch.spark.sql") \
                    .option("es.nodes", "elasticsearch") \
                    .option("es.port", "9200") \
                    .option("es.resource", "spark_data") \
                    .mode("append") \
                    .save()
                
                print(f"[SUCCESS] Successfully processed and indexed: {file}")
            
            except Exception as file_err:
                print(f"[ERROR] Failed to process file {file}: {file_err}")

        print("[INFO] Stopping Spark session.")
        spark.stop()

    except Exception as e:
        print(f"[FATAL] Spark processing failed: {e}")
        return f"Failed: {e}"

    print("=== All files processed and written to Elasticsearch ===")
    return "All files processed sequentially and written to Elasticsearch"

def save_to_es(**kwargs):
    ti = kwargs['ti']
    data = ti.xcom_pull(task_ids='spark_task2')

    print("[INFO] Connecting to Elasticsearch...")
    es = Elasticsearch("http://elasticsearch:9200")
    
    for idx, doc in enumerate(data):
        try:
            es.index(index='spark_data', body=doc)
            print(f"[INFO] Indexed document {idx + 1}")
        except Exception as err:
            print(f"[ERROR] Failed to index document {idx + 1}: {err}")

with DAG(
    'POC_orange_data2',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:

    spark_task = PythonOperator(
        task_id='spark_task2',
        python_callable=spark_processing
    )

    es_task = PythonOperator(
        task_id='es_task',
        python_callable=save_to_es,
        provide_context=True
    )

    spark_task
