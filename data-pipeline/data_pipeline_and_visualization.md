# Data Pipeline and Visualization Setup for Elastic Stack SIEM

This document provides comprehensive guidance on configuring data pipelines and creating effective visualizations for your Elastic Stack SIEM implementation. It covers data sources, ingestion methods, pipeline configurations, and dashboard creation.

## Table of Contents

1. [Data Sources Overview](#data-sources-overview)
2. [Data Ingestion Methods](#data-ingestion-methods)
3. [Logstash Pipeline Configuration](#logstash-pipeline-configuration)
4. [Elasticsearch Index Management](#elasticsearch-index-management)
5. [Kibana Visualization Setup](#kibana-visualization-setup)
6. [SIEM Dashboard Creation](#siem-dashboard-creation)
7. [Alert Configuration](#alert-configuration)
8. [Data Retention and Lifecycle Management](#data-retention-and-lifecycle-management)

## Data Sources Overview

The Elastic Stack SIEM solution collects data from various sources to provide comprehensive security monitoring. The primary data sources include:

### System Logs
- Authentication logs (SSH, sudo, etc.)
- System logs (kernel, services, etc.)
- Application logs (web servers, databases, etc.)

### Network Data
- Network traffic (packets, flows, etc.)
- Firewall logs
- DNS queries and responses
- HTTP/HTTPS traffic

### Security-Specific Data
- Endpoint security events
- Intrusion detection/prevention system alerts
- Vulnerability scan results
- Threat intelligence feeds

### Windows-Specific Data (for Windows team members)
- Windows Event Logs
- Sysmon events
- PowerShell logs
- WMI activity logs

## Data Ingestion Methods

The Elastic Stack SIEM solution uses various methods to ingest data from different sources:

### Beats Agents

Beats are lightweight data shippers that collect specific types of data:

1. **Filebeat**: Collects log files from the filesystem
   - System logs
   - Application logs
   - Custom log files

2. **Packetbeat**: Collects network traffic data
   - Protocol-specific data (HTTP, DNS, MySQL, etc.)
   - Network flow data
   - TLS/SSL information

3. **Auditbeat**: Collects system audit data
   - File integrity monitoring
   - System module (users, processes, sockets, etc.)
   - Auditd module (system calls, file access, etc.)

4. **Winlogbeat**: Collects Windows event logs (for Windows team members)
   - Security events
   - System events
   - Application events
   - Sysmon events
   - PowerShell logs

### Logstash

Logstash serves as a central data processing pipeline that:
- Receives data from Beats and other sources
- Processes and transforms the data
- Enriches the data with additional information
- Outputs the processed data to Elasticsearch

### Direct API Ingestion

For some data sources, direct API ingestion to Elasticsearch may be used:
- Custom applications
- Third-party security tools
- Cloud service logs

## Logstash Pipeline Configuration

Logstash pipelines are configured to process and enrich data before indexing in Elasticsearch. The following sections describe the key pipeline configurations:

### Authentication Events Pipeline

```
input {
  beats {
    port => 5044
    ssl => false
  }
}

filter {
  if [event][module] == "system" {
    if [event][dataset] == "auth" {
      grok {
        match => { "message" => "%{SYSLOGTIMESTAMP:timestamp} %{SYSLOGHOST:hostname} %{DATA:program}(?:\[%{POSINT:pid}\])?: %{GREEDYDATA:message}" }
      }
      
      # Extract authentication events
      if [message] =~ "Failed password" {
        mutate {
          add_tag => [ "authentication_failure" ]
        }
        grok {
          match => { "message" => "Failed password for %{USERNAME:user} from %{IP:source_ip}" }
        }
      }
      else if [message] =~ "Accepted password" {
        mutate {
          add_tag => [ "authentication_success" ]
        }
        grok {
          match => { "message" => "Accepted password for %{USERNAME:user} from %{IP:source_ip}" }
        }
      }
    }
  }
  
  # Add GeoIP information for IP addresses
  if [source_ip] {
    geoip {
      source => "source_ip"
      target => "source_geo"
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    user => "elastic"
    password => "${ELASTIC_PASSWORD}"
    index => "%{[@metadata][beat]}-%{[@metadata][version]}-%{+YYYY.MM.dd}"
    ssl => false
  }
}
```

### Network Traffic Pipeline

Create a new file at `/home/ubuntu/elastic-stack-siem/docker/logstash/pipeline/network.conf` with the following content:

```
input {
  beats {
    port => 5045
    ssl => false
    type => "network"
  }
}

filter {
  if [type] == "network" {
    # Process HTTP traffic
    if [http] {
      # Identify potential web attacks
      if [http][request][body] =~ /(?i)(union\s+select|exec\s+xp_|'--|\%27|\%2527|<script>|javascript:)/ {
        mutate {
          add_tag => [ "potential_sql_injection", "attack" ]
        }
      }
      
      # Identify suspicious user agents
      if [user_agent][original] =~ /(?i)(sqlmap|nikto|nmap|burpsuite|hydra|gobuster|dirbuster)/ {
        mutate {
          add_tag => [ "suspicious_user_agent", "attack" ]
        }
      }
    }
    
    # Process DNS traffic
    if [dns] {
      # Identify potential DNS tunneling
      if [dns][question][name] =~ /[a-zA-Z0-9]{30,}/ {
        mutate {
          add_tag => [ "potential_dns_tunneling", "attack" ]
        }
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    user => "elastic"
    password => "${ELASTIC_PASSWORD}"
    index => "packetbeat-%{+YYYY.MM.dd}"
    ssl => false
  }
}
```

### Windows Events Pipeline

Create a new file at `/home/ubuntu/elastic-stack-siem/docker/logstash/pipeline/windows.conf` with the following content:

```
input {
  beats {
    port => 5046
    ssl => false
    type => "windows"
  }
}

filter {
  if [type] == "windows" {
    # Process Windows security events
    if [event][code] == 4624 {
      mutate {
        add_tag => [ "user_logon" ]
      }
    }
    else if [event][code] == 4625 {
      mutate {
        add_tag => [ "logon_failure" ]
      }
    }
    else if [event][code] == 4720 {
      mutate {
        add_tag => [ "user_created" ]
      }
    }
    else if [event][code] == 4732 {
      mutate {
        add_tag => [ "user_added_to_group" ]
      }
    }
    
    # Process PowerShell events
    if [event][provider] == "Microsoft-Windows-PowerShell" {
      if [event][code] == 4104 {
        mutate {
          add_tag => [ "powershell_script" ]
        }
        
        # Identify potentially malicious PowerShell commands
        if [event][message] =~ /(?i)(Invoke-Expression|IEX|Invoke-Mimikatz|Invoke-Shellcode|New-Object Net\.WebClient|DownloadString|DownloadFile|Start-Process|Hidden)/ {
          mutate {
            add_tag => [ "suspicious_powershell", "attack" ]
          }
        }
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    user => "elastic"
    password => "${ELASTIC_PASSWORD}"
    index => "winlogbeat-%{+YYYY.MM.dd}"
    ssl => false
  }
}
```

## Elasticsearch Index Management

Proper index management is crucial for efficient data storage and retrieval. The following sections describe the key index management configurations:

### Index Lifecycle Management (ILM)

Create an ILM policy to manage the lifecycle of your indices:

1. In Kibana, navigate to **Stack Management** > **Index Lifecycle Policies**
2. Click **Create policy**
3. Name the policy `siem-logs-policy`
4. Configure the following phases:
   - **Hot**: Set the maximum size to 50GB or maximum age to 1 day
   - **Warm**: Move to warm storage after 7 days
   - **Cold**: Move to cold storage after 30 days
   - **Delete**: Delete after 90 days (adjust based on your retention requirements)

### Index Templates

Create index templates to define mappings and settings for your indices:

1. In Kibana, navigate to **Stack Management** > **Index Templates**
2. Click **Create template**
3. Name the template `siem-logs-template`
4. Set the index pattern to `filebeat-*,packetbeat-*,auditbeat-*,winlogbeat-*`
5. Configure the following settings:
   ```json
   {
     "index": {
       "lifecycle": {
         "name": "siem-logs-policy",
         "rollover_alias": "siem-logs"
       },
       "number_of_shards": 1,
       "number_of_replicas": 1
     }
   }
   ```
6. Define mappings for common fields (optional)
7. Click **Create template**

## Kibana Visualization Setup

Kibana provides powerful visualization capabilities for analyzing security data. The following sections describe how to create effective visualizations:

### Creating Visualizations

1. In Kibana, navigate to **Visualize**
2. Click **Create visualization**
3. Choose the visualization type (e.g., bar chart, pie chart, heatmap, etc.)
4. Select the index pattern (e.g., `filebeat-*`, `packetbeat-*`, etc.)
5. Configure the visualization settings:
   - Metrics (e.g., count, average, sum, etc.)
   - Buckets (e.g., date histogram, terms, filters, etc.)
   - Options (e.g., colors, labels, etc.)
6. Save the visualization with a descriptive name

### Key Visualizations for SIEM

#### Authentication Failures Visualization

1. Create a new visualization of type **Line**
2. Select the index pattern `filebeat-*`
3. Configure the Y-axis metric to **Count**
4. Configure the X-axis bucket to **Date Histogram** with field `@timestamp`
5. Add a **Filters** bucket with the filter `tags: authentication_failure`
6. Save the visualization as `Authentication Failures Over Time`

#### Network Traffic by Protocol Visualization

1. Create a new visualization of type **Pie**
2. Select the index pattern `packetbeat-*`
3. Configure the metric to **Count**
4. Configure the bucket to **Terms** with field `network.protocol`
5. Save the visualization as `Network Traffic by Protocol`

#### Top Source IP Addresses Visualization

1. Create a new visualization of type **Data Table**
2. Select the index pattern `filebeat-*,packetbeat-*`
3. Configure the metric to **Count**
4. Configure the bucket to **Terms** with field `source.ip`
5. Add a **Terms** sub-bucket with field `event.action`
6. Save the visualization as `Top Source IP Addresses`

#### Suspicious PowerShell Commands Visualization

1. Create a new visualization of type **Data Table**
2. Select the index pattern `winlogbeat-*`
3. Configure the metric to **Count**
4. Configure the bucket to **Terms** with field `event.message`
5. Add a filter for `tags: suspicious_powershell`
6. Save the visualization as `Suspicious PowerShell Commands`

## SIEM Dashboard Creation

Dashboards combine multiple visualizations to provide a comprehensive view of your security posture. The following sections describe how to create effective SIEM dashboards:

### Creating Dashboards

1. In Kibana, navigate to **Dashboard**
2. Click **Create dashboard**
3. Click **Add** to add visualizations to the dashboard
4. Select the visualizations you want to add
5. Arrange the visualizations on the dashboard
6. Save the dashboard with a descriptive name

### Key Dashboards for SIEM

#### Security Overview Dashboard

Create a dashboard named `Security Overview` with the following visualizations:
- Authentication Failures Over Time
- Network Traffic by Protocol
- Top Source IP Addresses
- Geographic Map of Source IPs
- Recent Security Events

#### Network Security Dashboard

Create a dashboard named `Network Security` with the following visualizations:
- Network Traffic Over Time
- Top Destination Ports
- DNS Query Types
- HTTP Response Codes
- Suspicious Network Activity

#### Host Security Dashboard

Create a dashboard named `Host Security` with the following visualizations:
- System Resource Usage
- File Integrity Changes
- User Activity
- Process Executions
- Suspicious Commands

#### Windows Security Dashboard

Create a dashboard named `Windows Security` with the following visualizations:
- Windows Logon Events
- PowerShell Activity
- User Account Changes
- Group Membership Changes
- Suspicious PowerShell Commands

## Alert Configuration

Alerts notify you of potential security incidents based on predefined conditions. The following sections describe how to configure effective alerts:

### Creating Detection Rules

1. In Kibana, navigate to **Security** > **Detections** > **Manage detection rules**
2. Click **Create rule**
3. Select the rule type (e.g., query, threshold, etc.)
4. Configure the rule settings:
   - Name and description
   - Index pattern
   - Query or threshold
   - Schedule
   - Actions (e.g., notifications)
5. Save and enable the rule

### Key Detection Rules for SIEM

#### Brute Force Attack Detection

1. Create a new rule of type **Threshold**
2. Configure the following settings:
   - Name: `Brute Force Attack Detection`
   - Description: `Detects potential brute force attacks based on failed authentication attempts`
   - Index pattern: `filebeat-*`
   - Query: `tags:authentication_failure`
   - Threshold: Count > 5 grouped by `source.ip` and `user.name` in 5 minutes
   - Schedule: Run every 5 minutes
   - Actions: Add notification action (e.g., email, Slack, etc.)

#### Suspicious PowerShell Activity

1. Create a new rule of type **Query**
2. Configure the following settings:
   - Name: `Suspicious PowerShell Activity`
   - Description: `Detects suspicious PowerShell commands that may indicate malicious activity`
   - Index pattern: `winlogbeat-*`
   - Query: `tags:suspicious_powershell`
   - Schedule: Run every 15 minutes
   - Actions: Add notification action (e.g., email, Slack, etc.)

#### Data Exfiltration Detection

1. Create a new rule of type **Threshold**
2. Configure the following settings:
   - Name: `Data Exfiltration Detection`
   - Description: `Detects potential data exfiltration based on unusual outbound traffic`
   - Index pattern: `packetbeat-*`
   - Query: `destination.ip:* AND NOT destination.ip:10.0.0.0/8 AND NOT destination.ip:172.16.0.0/12 AND NOT destination.ip:192.168.0.0/16`
   - Threshold: Sum of `network.bytes` > 100000000 grouped by `source.ip` in 1 hour
   - Schedule: Run every 15 minutes
   - Actions: Add notification action (e.g., email, Slack, etc.)

## Data Retention and Lifecycle Management

Proper data retention and lifecycle management are crucial for efficient resource utilization. The following sections describe how to configure data retention policies:

### Index Lifecycle Management

Configure ILM policies to manage the lifecycle of your indices as described in the [Index Lifecycle Management](#index-lifecycle-management) section.

### Data Retention Considerations

Consider the following factors when determining your data retention policy:
- Regulatory requirements (e.g., PCI DSS, HIPAA, etc.)
- Organizational policies
- Storage capacity
- Performance requirements
- Investigation needs

### Recommended Retention Periods

- **Hot tier**: 7-30 days (for active analysis)
- **Warm tier**: 30-90 days (for recent investigations)
- **Cold tier**: 90-365 days (for historical analysis)
- **Frozen/Delete**: After 365 days (or as required by regulations)

Adjust these periods based on your specific requirements and available resources.

## Conclusion

This document has provided comprehensive guidance on configuring data pipelines and creating effective visualizations for your Elastic Stack SIEM implementation. By following these guidelines, you can establish a robust security monitoring solution that provides visibility into potential security incidents and helps protect your organization's assets.

For specific implementation details, refer to the [Deployment Guide](../docker/DEPLOYMENT.md) and the [Scenario Documentation](../scenarios/README.md).

