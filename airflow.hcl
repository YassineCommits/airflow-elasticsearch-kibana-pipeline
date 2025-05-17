job "airflow" {
  datacenters = ["us-west-aws"]
  node_pool   = "us-west-aws"
  type        = "service"

  constraint {
    attribute = "${node.pool}"
    value     = "us-west-aws"
  }
  constraint {
    attribute = "${meta.compute}"
    value     = "true"
  }
  constraint {
    attribute = "${meta.datacenter}"
    value     = "us-west-aws"
  }
  constraint {
    attribute = "${meta.storage}"
    value     = "false"
  }

  # PostgreSQL Database Group
  group "postgres" {
    network {
      mode = "host"
      port "db" {
        static = 5432
      }
    }

    task "postgres" {
      driver = "docker"
      config {
        image = "postgres:13"
        ports = ["db"]
        volumes = [
          "/tank/pg_data:/var/lib/postgresql/data:rw,z"
        ]
      }
      env {
        POSTGRES_USER     = "airflow"
        POSTGRES_PASSWORD = "airflow"
        POSTGRES_DB       = "airflow"
      }
      resources {
        cpu    = 1000
        memory = 1024
      }
    }
  }

  # Airflow Webserver Group
  group "webserver" {
    network {
      port "http" { to = 8080 }
    }

    task "airflow-init-db" {
      driver = "docker"
      lifecycle {
        hook = "prestart"
      }
      config {
        image = "apache/airflow:2.7.3"
        entrypoint = ["/bin/bash", "-c"]
        args = ["airflow db init"]
        volumes = [
          "/tank/dags:/opt/airflow/dags:rw,z",
          "/tank/logs:/opt/airflow/logs:rw,z",
          "/tank/plugins:/opt/airflow/plugins:rw,z"
        ]
      }
      env {
        AIRFLOW__CORE__EXECUTOR             = "LocalExecutor"
        AIRFLOW__DATABASE__SQL_ALCHEMY_CONN = "postgresql+psycopg2://airflow:airflow@10.186.7.170:5432/airflow"
        AIRFLOW_CONN_ELASTICSEARCH_DEFAULT  = "http://10.186.7.239:9200"
        JAVA_HOME                           = "/usr/lib/jvm/java-11-openjdk-amd64"
      }
      resources {
        cpu    = 300
        memory = 500
      }
    }

    task "airflow-create-admin" {
      driver = "docker"
      lifecycle {
        hook = "prestart"
      }
      config {
        image = "apache/airflow:2.7.3"
        entrypoint = ["/bin/bash", "-c"]
        args = [
          "until airflow users create --username airflow --password airflow --firstname Airflow --lastname Admin --role Admin --email admin@example.com; do sleep 2; done"
        ]
        volumes = [
          "/tank/dags:/opt/airflow/dags:rw,z",
          "/tank/logs:/opt/airflow/logs:rw,z",
          "/tank/plugins:/opt/airflow/plugins:rw,z"
        ]
      }
      env {
        AIRFLOW__CORE__EXECUTOR             = "LocalExecutor"
        AIRFLOW__DATABASE__SQL_ALCHEMY_CONN = "postgresql+psycopg2://airflow:airflow@10.186.7.170:5432/airflow"
        AIRFLOW_CONN_ELASTICSEARCH_DEFAULT  = "http://10.186.7.239:9200"
        JAVA_HOME                           = "/usr/lib/jvm/java-11-openjdk-amd64"
      }
      resources {
        cpu    = 300
        memory = 500
      }
    }

    task "webserver" {
      driver = "docker"
      config {
        image = "apache/airflow:2.7.3"
        args  = ["webserver"]
        ports = ["http"]
        volumes = [
          "/tank/dags:/opt/airflow/dags:rw,z",
          "/tank/logs:/opt/airflow/logs:rw,z",
          "/tank/plugins:/opt/airflow/plugins:rw,z"
        ]
      }
      env {
        AIRFLOW__CORE__EXECUTOR             = "LocalExecutor"
        AIRFLOW__DATABASE__SQL_ALCHEMY_CONN = "postgresql+psycopg2://airflow:airflow@10.186.7.170:5432/airflow"
        AIRFLOW__CORE__LOAD_EXAMPLES        = "False"
        AIRFLOW_CONN_ELASTICSEARCH_DEFAULT  = "http://10.186.7.239:9200"
        JAVA_HOME                           = "/usr/lib/jvm/java-11-openjdk-amd64"
      }
      resources {
        cpu    = 1000
        memory = 3000
      }
    }
  }

  # Airflow Scheduler Group
  group "scheduler" {
    task "scheduler" {
      driver = "docker"
      config {
        image = "apache/airflow:2.7.3"
        args  = ["scheduler"]
        volumes = [
          "/tank/dags:/opt/airflow/dags:rw,z",
          "/tank/logs:/opt/airflow/logs:rw,z",
          "/tank/plugins:/opt/airflow/plugins:rw,z"
        ]
      }
      env {
        AIRFLOW__CORE__EXECUTOR             = "LocalExecutor"
        AIRFLOW__DATABASE__SQL_ALCHEMY_CONN = "postgresql+psycopg2://airflow:airflow@10.186.7.170:5432/airflow"
        AIRFLOW_CONN_ELASTICSEARCH_DEFAULT  = "http://10.186.7.239:9200"
        JAVA_HOME                           = "/usr/lib/jvm/java-11-openjdk-amd64"
      }
      resources {
        cpu    = 1000
        memory = 3000
      }
    }
  }
}
