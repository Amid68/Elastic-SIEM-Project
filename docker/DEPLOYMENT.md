# Elastic Stack SIEM Deployment Guide

This guide provides step-by-step instructions for deploying the Elastic Stack SIEM solution using Docker.

## Prerequisites

- M1 Mac or Linux distribution with Docker installed
- At least 4GB of RAM allocated to Docker
- Git (for cloning the repository)
- Basic understanding of Docker and containerization
- Terminal access

## Step 1: Clone the Repository

```bash
sudo git clone https://github.com/Amid68/Elastic-SIEM-Project.git
cd Elastic-SIEM-Project
```

## Step 2: Configure Environment Variables

1. Navigate to the docker directory:
   ```bash
   cd docker
   ```

2. Create the `.env` file with the following content:
   ```bash
   # Create the .env file
   sudo cat > .env << 'EOL'
   # Environment variables for Elastic Stack SIEM deployment
   # Elasticsearch credentials
   ELASTIC_PASSWORD=elastic123
   # Elasticsearch heap size (adjust based on available memory)
   ES_JAVA_OPTS=-Xms512m -Xmx512m
   # Kibana settings
   KIBANA_ENCRYPTION_KEY=AQflBkD7h6iXZ08tv1BdenhUvDw7uInr17pnU6524q4=
   # Stack version
   STACK_VERSION=8.12.2
   # Set the cluster name
   CLUSTER_NAME=elastic-siem-cluster
   # Memory limits
   MEM_LIMIT=1073741824  # 1GB in bytes
   EOL
   ```

3. If not on M1 Mac, remove or comment out the platform-specific settings in docker-compose.yml:
   ```bash
   # Open docker-compose.yml and comment out or remove lines containing:
   # platform: linux/arm64
   ```

## Step 3: Deploy the Elastic Stack

1. Start the Elasticsearch container:
   ```bash
   sudo docker-compose up -d elasticsearch
   ```

2. Wait for Elasticsearch to fully initialize (this may take a few minutes):
   ```bash
   sudo docker-compose logs -f elasticsearch
   ```
   
   Wait until you see logs indicating that the service is running properly. Note that a YELLOW status is normal for a single-node cluster.

## Step 4: Set Up Authentication

This critical step ensures that Kibana can successfully connect to Elasticsearch:

1. Once Elasticsearch is running, set up the built-in users:
   ```bash
   # Access the Elasticsearch container
   sudo docker exec -it elasticsearch bash

   # Set the password for the kibana_system user
   bin/elasticsearch-reset-password -u kibana_system --interactive
   # Enter the password "kibana123" when prompted

   # Also ensure the elastic superuser password matches your .env file
   bin/elasticsearch-reset-password -u elastic --interactive
   # Enter the password "elastic123" when prompted

   # Exit the container
   exit
   ```

## Step 5: Deploy Remaining Components

1. Deploy Kibana:
   ```bash
   sudo docker-compose up -d --no-deps kibana
   ```
   
   The `--no-deps` flag bypasses dependency checks that might incorrectly mark Elasticsearch as unhealthy.

2. After Kibana is running, deploy Logstash:
   ```bash
   sudo docker-compose up -d --no-deps logstash
   ```

3. Finally, deploy the Beats components:
   ```bash
   sudo docker-compose up -d --no-deps filebeat
   ```

## Step 6: Verify All Components Are Running

1. Check the status of all containers:
   ```bash
   sudo docker-compose ps
   ```

2. Check logs for any errors:
   ```bash
   sudo docker-compose logs kibana
   ```

3. If Kibana shows "server is not ready yet" or authentication failures:
   ```bash
   # Verify Elasticsearch is accessible from Kibana
   sudo docker exec -it kibana curl -u elastic:elastic123 http://elasticsearch:9200
   
   # If that fails, double-check your authentication setup from Step 4
   ```

## Step 7: Access Kibana

1. Open a web browser and navigate to:
   ```
   http://localhost:5601
   ```

2. Log in with the following credentials:
   - Username: `elastic`
   - Password: `elastic123`

## Step 8: Configure Kibana for SIEM

1. After logging in to Kibana, click on the hamburger menu (☰) in the top-left corner.

2. Navigate to "Security" in the left sidebar.

3. If this is your first time, you'll be prompted to add sample data. You can choose to add it for testing purposes.

4. Configure detection rules:
   - Go to "Security" > "Detections" > "Manage detection rules"
   - Enable the rules relevant to your monitoring needs
   - Create custom rules as needed

## Step 9: Troubleshooting

If you encounter any issues:

1. Authentication issues:
   ```bash
   # Reset passwords again if needed
   sudo docker exec -it elasticsearch bash
   bin/elasticsearch-reset-password -u kibana_system --interactive
   bin/elasticsearch-reset-password -u elastic --interactive
   exit
   ```

2. Container connection issues:
   ```bash
   # Check the network
   sudo docker network inspect elastic-net
   
   # Restart specific containers
   sudo docker-compose restart kibana
   ```

3. For any other issues, check the logs:
   ```bash
   sudo docker-compose logs elasticsearch
   sudo docker-compose logs kibana
   sudo docker-compose logs logstash
   ```

## Step 10: Stopping the Elastic Stack

To stop the Elastic Stack when not in use:

```bash
sudo docker-compose down
```

To stop and remove all data (use with caution):

```bash
sudo docker-compose down -v
```
