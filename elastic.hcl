job "elasticsearch" {
  datacenters = ["us-west-aws"]
  node_pool   = "us-west-aws" // Good to have for clarity
  type        = "service"

  constraint {
    attribute = "${node.pool}"
    value     = "us-west-aws"
  }
  constraint {
    attribute = "${meta.storage}"
    value     = "true"
  }
  constraint {
    attribute = "${meta.datacenter}"
    value     = "us-west-aws"
  }

  group "elasticsearch" {
    count = 1

    network {
      port "http" {
        static = 9200
        to     = 9200 // Explicitly map container port
      }
    }

    # Removed the group-level volume "elasticsearch_data" block

    task "elasticsearch" {
      driver = "docker"

      config {
        image = "elasticsearch:8.12.0"
        ports = ["http"]

        # Direct host path volume mount:
        # Assumes /tank/elastic exists on your Nomad client node af657013
        volumes = [
          "/tank/elastic-sequence-nocompress:/usr/share/elasticsearch/data",
        ]
      }

      # Removed the volume_mount block that referenced the group volume

      env = {
        "discovery.type"         = "single-node", // Ensure quotes if keys have dots or dashes
        "xpack.security.enabled" = "false"
        // It's good practice to also set ES_JAVA_OPTS here, e.g.:
        // "ES_JAVA_OPTS"           = "-Xms1g -Xmx1g"
      }

      resources {
        cpu    = 500  // MHz
        memory = 2048 // MB
      }

      service {
        name = "elasticsearch-svc" // Changed to be more specific for service discovery
        tags = ["elasticsearch"]
        port = "http"

        // Optional: Add a health check for Elasticsearch
        check {
          type     = "http"
          path     = "/_cluster/health"
          interval = "20s"
          timeout  = "3s"
        }
      }
    }
  }
}