# Data Pipeline PoC

## Overview
This Proof of Concept (PoC) aims to build a robust data pipeline to collect, process, and visualize Key Performance Indicators (KPIs) from Orange’s network nodes and services. The architecture follows an Extract, Load, Transform (ELT) workflow, leveraging modern tools to ensure scalability, reliability, and real-time insights.

## Setup
### Repository
Clone the repository:
```
git clone https://github.com/Guepard-Corp/Data_pipeline.git
cd Data_pipeline
```
### Create a folder in the root directory named data
Download the csv file and copy it into the directory /data
https://www.kaggle.com/datasets/sebastianwillmann/beverage-sales


### Running the Pipeline
Start the services:
```
docker-compose up --build
```

Initialize the Airflow database:
```
docker-compose run airflow-webserver airflow db init
```

Create an Airflow admin user:
```
docker-compose run airflow-webserver airflow users create --username airflow --password airflow --firstname Airflow --lastname Admin --role Admin --email admin@example.com
```

## Querying ELK
To retrieve processed data from ELK, run the following command:
```
curl -X GET "http://localhost:9200/spark_data/_search?pretty=true"
```

