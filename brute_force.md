# Brute-Force Attack Detection with Elastic SIEM: Step-by-Step Guide

This guide walks through setting up a brute-force attack simulation environment and configuring Elastic SIEM to detect these attacks. The simulation helps understand how attackers attempt to gain unauthorized access through password guessing and how a SIEM can detect and alert on such activities.

## 1. Repository Structure

Ensure your repository structure includes these essential components:

```
.
├── docker
│   ├── docker-compose.yml
│   ├── elasticsearch/
│   ├── filebeat/
│   │   ├── filebeat.yml
│   │   └── filebeat-ssh.yml   # We'll create this
│   ├── kibana/
│   ├── logstash/
│   │   ├── config/
│   │   └── pipeline/
│   │       └── beats.conf     # We'll modify this
│   └── simulation/
│       └── run-brute-force.sh # We'll create this
```

## 2. Configure SSH Target Container

Add the SSH target container configuration to your `docker-compose.yml` file:

```yaml
# SSH Target (for brute-force simulation)
ssh-target:
  image: linuxserver/openssh-server
  container_name: ssh-target
  environment:
    - PUID=1000
    - PGID=1000
    - TZ=Etc/UTC
    - USER_NAME=testuser
    - PASSWORD_ACCESS=true
    - USER_PASSWORD=testpassword
    - LOG_STDOUT=true  # This ensures SSH logs go to stdout
  ports:
    - "2222:2222"
  networks:
    - elastic-net
  platform: linux/arm64  # Change based on your architecture
  labels:
    co.elastic.logs/module: "system"
    co.elastic.logs/fileset: "auth"
```

Add an attacker container that will run Hydra:

```yaml
# Hydra Attacker Container
hydra-attacker:
  image: ubuntu
  container_name: hydra-attacker
  tty: true
  stdin_open: true
  command: bash -c "apt-get update && apt-get install -y hydra && sleep infinity"
  networks:
    - elastic-net
  platform: linux/arm64  # Change based on your architecture
```

## 3. Update Logstash Pipeline Configuration

Modify the `docker/logstash/pipeline/beats.conf` file to recognize and parse SSH authentication logs:

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
  
  # SSH container-specific parsing
  if [tags] and [tags] =~ "ssh" {
    grok {
      match => { "message" => "%{SYSLOGTIMESTAMP:timestamp} %{GREEDYDATA:ssh_log}" }
    }
    
    if [ssh_log] =~ "Failed password" {
      mutate {
        add_tag => [ "authentication_failure" ]
      }
      grok {
        match => { "ssh_log" => "Failed password for %{USERNAME:user} from %{IP:source_ip}" }
      }
    }
    else if [ssh_log] =~ "Accepted password" {
      mutate {
        add_tag => [ "authentication_success" ]
      }
      grok {
        match => { "ssh_log" => "Accepted password for %{USERNAME:user} from %{IP:source_ip}" }
      }
    }
  }
  
  # Check for Docker container logs with SSH auth messages
  if [container][name] =~ "ssh-target" or [container][image][name] =~ "openssh-server" {
    if [message] =~ "Failed password" {
      mutate {
        add_tag => [ "authentication_failure" ]
      }
      grok {
        match => { "message" => ".*Failed password for %{USERNAME:user} from %{IP:source_ip}.*" }
      }
    }
    else if [message] =~ "Accepted password" {
      mutate {
        add_tag => [ "authentication_success" ]
      }
      grok {
        match => { "message" => ".*Accepted password for %{USERNAME:user} from %{IP:source_ip}.*" }
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

## 4. Create Brute-Force Simulation Script

Create a file `docker/simulation/run-brute-force.sh` with the following content:

```bash
#!/bin/bash

echo "Starting brute-force attack with Hydra..."
echo "This will generate failed login attempts that should be visible in Elastic SIEM"

# Create password list for the brute-force attack
docker exec hydra-attacker bash -c "echo 'password123' > /tmp/passwords.txt"
docker exec hydra-attacker bash -c "echo 'admin' >> /tmp/passwords.txt"
docker exec hydra-attacker bash -c "echo '123456' >> /tmp/passwords.txt" 
docker exec hydra-attacker bash -c "echo 'testpassword' >> /tmp/passwords.txt" # The correct password

# Find the IP address of the ssh-target container
SSH_TARGET_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ssh-target)

echo "Target SSH Server IP: $SSH_TARGET_IP"

# Run Hydra attack with 1 thread (more controlled)
docker exec hydra-attacker hydra -l testuser -P /tmp/passwords.txt $SSH_TARGET_IP -s 2222 ssh -V -t 1

echo "Attack simulation completed."
echo "Verifying logs made it to Elasticsearch..."

# Wait 10 seconds for log processing
sleep 10

# Check logs directly in SSH container
echo "SSH Container Log Contents:"
docker exec ssh-target cat /var/log/auth.log || echo "No auth.log found"
docker logs ssh-target | grep -i password

echo "Check Elastic SIEM for alerts."
```

Make the script executable:

```bash
chmod +x docker/simulation/run-brute-force.sh
```

## 5. Configure Kibana Detection Rule

1. Log in to Kibana at `http://localhost:5601`
2. Navigate to **Security** > **Rules** > **Create new rule**

3. Select **Threshold** rule type:

![Rule Type Selection](placeholder-rule-type.png)

4. Define the rule:
   - **Index patterns**: Include filebeat-* patterns
   - **Custom query**: `tags:authentication_failure OR message:*Failed password* OR message:*authentication failure*`
   - **Group by field**: `source.ip`
   - **Threshold**: 3
   - **Timeframe**: 5 minutes

![Rule Definition](placeholder-rule-definition.png)

5. Configure rule settings:
   - **Rule name**: "Brute-Force Attack Detection"
   - **Risk score**: 73
   - **Severity**: High
   - **Tags**: "brute-force", "authentication", "credential-access"
   - **MITRE ATT&CK**: Select "Credential Access" and "Brute Force (T1110)"
   - **False positive examples**: Add "Users who forgot passwords and made multiple attempts"

![Rule Settings](placeholder-rule-settings.png)

6. Set schedule:
   - **Runs every**: 5m
   - **Additional look-back time**: 1m

7. Save and enable the rule

## 6. Deploy and Run Simulation

1. Start or restart the components:

```bash
cd docker
docker-compose restart logstash filebeat ssh-target
```

2. Wait for components to start (around 30 seconds):

```bash
sleep 30
```

3. Run the brute-force simulation:

```bash
./simulation/run-brute-force.sh
```

4. Check Kibana for alerts:
   - Navigate to **Security** > **Alerts**
   - You should see an alert for "Brute-Force Attack Detection"

![Alert Detection](placeholder-alert-detection.png)

## 7. Analyzing the Alert

The alert shows:
- Multiple failed login attempts from the same IP address
- A timeline of the attack
- The exact authentication failure events
- The source IP address that initiated the attack
- The targeted username

You can click on the alert to see more details, including:
- All source and destination IP addresses
- All authentication attempts (failures and successes)
- Timestamps for each event

![Alert Details](placeholder-alert-details.png)

## 8. Troubleshooting

If you don't see alerts:

1. Check Logstash logs:
```bash
docker logs logstash
```

2. Check Filebeat logs:
```bash
docker logs filebeat
```

3. Verify logs are getting to Elasticsearch:
```bash
curl -u elastic:elastic123 "http://localhost:9200/_search?q=tags:authentication_failure&pretty"
```

4. Verify your detection rule is enabled:
   - Go to Security > Rules
   - Check the status of your "Brute-Force Attack Detection" rule

## Conclusion

You have successfully set up a brute-force attack simulation environment and configured Elastic SIEM to detect these attacks. This hands-on experience demonstrates how security information and event management (SIEM) systems can identify and alert on potential security threats in real-time.

The simulation helps security professionals understand:
- How brute-force attacks are executed
- How to configure detection rules for authentication failures
- How to analyze security alerts in Elastic SIEM
- The importance of log collection and processing in security monitoring

This knowledge can be applied to enhance security monitoring in production environments and develop more sophisticated detection and response strategies.
