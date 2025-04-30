# Kibana Visualization Templates for Elastic Stack SIEM

This directory contains visualization templates and dashboard configurations for the Elastic Stack SIEM implementation. These templates can be imported into Kibana to quickly set up effective security monitoring dashboards.

## Visualization Templates

The following visualization templates are provided:

- `auth_failures.ndjson`: Authentication failures over time
- `network_traffic.ndjson`: Network traffic by protocol
- `top_source_ips.ndjson`: Top source IP addresses
- `suspicious_powershell.ndjson`: Suspicious PowerShell commands
- `geo_map.ndjson`: Geographic map of source IPs

## Dashboard Templates

The following dashboard templates are provided:

- `security_overview.ndjson`: Security overview dashboard
- `network_security.ndjson`: Network security dashboard
- `host_security.ndjson`: Host security dashboard
- `windows_security.ndjson`: Windows security dashboard

## Importing Templates

To import these templates into Kibana:

1. In Kibana, navigate to **Stack Management** > **Saved Objects**
2. Click **Import**
3. Select the `.ndjson` file you want to import
4. Click **Import**

## Creating Custom Visualizations

The `data_pipeline_and_visualization.md` document provides detailed instructions on creating custom visualizations and dashboards for your specific security monitoring needs.

