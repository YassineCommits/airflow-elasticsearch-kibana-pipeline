FROM apache/airflow:2.7.3

# Install Java and Spark dependencies
USER root
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow
RUN pip install --no-cache-dir \
    pyspark==3.5.0 \
    apache-airflow-providers-elasticsearch \
    elasticsearch==8.12.0