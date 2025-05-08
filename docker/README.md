# Docker Deployment Configuration for Elastic Stack SIEM

This directory contains the Docker configuration files needed to deploy the Elastic Stack SIEM solution on an M1 Mac environment. The configuration is designed to be compatible with ARM64 architecture while maintaining cross-platform compatibility for team members using Windows.

## Directory Structure

- `docker-compose.yml`: Main Docker Compose file for deploying the Elastic Stack
- `elasticsearch/`: Configuration files for Elasticsearch
- `kibana/`: Configuration files for Kibana
- `logstash/`: Configuration files for Logstash and pipeline configurations
- `filebeat/`: Configuration files for Filebeat
- `packetbeat/`: Configuration files for Packetbeat
- `.env`: Environment variables for Docker Compose

## Deployment Instructions

Detailed step-by-step instructions for deploying the Elastic Stack SIEM solution are provided in the [Deployment Guide](./DEPLOYMENT.md).

