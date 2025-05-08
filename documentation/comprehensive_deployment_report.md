# Elastic Stack SIEM Implementation
# Deployment Report

## Executive Summary

I successfully deployed an Elastic Stack SIEM (Security Information and Event Management) solution using Docker containers on an M1 Mac. This report documents the deployment process, including specific challenges encountered and their solutions.

## Project Scope

The deployment included the following components:
- Elasticsearch for data storage and search
- Kibana for visualization and security interface
- Logstash for data processing and enrichment
- Filebeat for log collection
- Packetbeat for network monitoring

The deployment initially included Auditbeat, but it was later removed due to ARM64 compatibility issues on M1 Macs.

## Architecture Overview

The deployed Elastic Stack SIEM solution follows a modular architecture where components work together to provide comprehensive security monitoring:

- **Elasticsearch** forms the core, storing and indexing all security data
- **Kibana** provides visualization and the security interface
- **Logstash** processes incoming data through configurable pipelines
- **Beats agents** collect data from various sources

I configured a Docker network for inter-component communication and exposed only necessary ports for external access.

## Deployment Process

### Initial Setup Challenges

The deployment started with trying to run Elasticsearch:

```bash
docker-compose up -d elasticsearch
```

I immediately encountered health check failures, though Elasticsearch itself was running. I determined that Docker was marking Elasticsearch as "unhealthy" despite it functioning properly with a "YELLOW" status (normal for single-node clusters).

### Authentication and Security Configuration

I made several critical adjustments to ensure proper component authentication:
1. Simplified the environment configuration with consistent passwords
2. Modified Docker health checks to accept "YELLOW" status:
   ```yaml
   healthcheck:
     test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health | grep -q '\"status\":\"green\"\\|\"status\":\"yellow\"'"]
   ```
3. Addressed SSL configuration issues by disabling security features for development

### Environment Variable Propagation

A key challenge was ensuring proper environment variable propagation between containers. Logstash failed to start with the error:
```
Cannot evaluate `${ELASTIC_PASSWORD}`. Replacement variable `ELASTIC_PASSWORD` is not defined
```

I solved this by explicitly adding the environment variable to the Logstash service definition in docker-compose.yml:

```yaml
environment:
  - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
```

### Component Deployment Work-Around

Due to health check issues, I deployed remaining components using the `--no-deps` flag:

```bash
docker-compose up -d --no-deps kibana
docker-compose up -d --no-deps logstash filebeat packetbeat
```

This bypassed the dependency check while allowing all components to connect properly.

## Configuration Summary

The final deployment consists of:

- **Elasticsearch**: Single-node cluster with YELLOW status
- **Kibana**: Accessible at http://localhost:5601
- **Logstash**: Processing data with custom pipelines
- **Filebeat**: Collecting system and application logs
- **Packetbeat**: Monitoring network traffic

Access credentials:
- URL: http://localhost:5601
- Username: elastic
- Password: elastic123

## Troubleshooting Guide

Based on my deployment experience, I identified common issues and solutions:

1. **Elasticsearch Health Status**: 
   - YELLOW status is normal for single-node clusters
   - Adjust health checks to accept this status

2. **Environment Variable Issues**:
   - Ensure variables are properly passed to all containers
   - Check pipeline configurations for variable references

3. **M1 Mac Compatibility**:
   - Specify platform: linux/arm64 for Docker images
   - Some components (like Auditbeat) have fundamental ARM64 limitations

4. **Authentication Failures**:
   - Verify consistent passwords across components
   - Check service account permissions

## Conclusion

This Elastic Stack SIEM deployment provides a solid foundation for security monitoring. Despite several configuration challenges, particularly related to environment variables, health checks, and M1 Mac compatibility, the system is now operational and ready for security monitoring activities.
