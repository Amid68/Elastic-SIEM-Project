# Elastic SIEM Project - Deployment

This repository contains the deployment configuration for an Elastic Stack SIEM (Security Information and Event Management) solution. The deployment is designed for M1 Mac environments with Docker, while maintaining compatibility for Windows team members.

## Project Overview

This project focuses on the **deployment** of the Elastic Stack for security monitoring. The deployment includes:

- Elasticsearch (8.12.2)
- Kibana (8.12.2)
- Logstash (8.12.2)
- Filebeat (8.12.2)
- Packetbeat (8.12.2)

## Repository Structure

- `/docker` - Contains all Docker configuration files and component configurations
- `/documentation` - Contains detailed documentation about the deployment process
- `generate_certs.sh` - Script for generating SSL certificates for secure communications

## Getting Started

For detailed deployment instructions, please refer to the [Deployment Guide](docker/DEPLOYMENT.md).

For a comprehensive report on the deployment process, including challenges and solutions, see the [Deployment Report](documentation/comprehensive_deployment_report.md).

## Important Notes

- This project is configured for M1 Mac (ARM64) architecture
- Windows compatibility is maintained through cross-platform configurations
- A single-node Elasticsearch deployment will show YELLOW status, which is normal

## Troubleshooting

Common deployment issues and their solutions are documented in the Deployment Guide's troubleshooting section.
