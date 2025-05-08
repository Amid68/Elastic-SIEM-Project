# Elastic Stack SIEM Deployment Guide

This guide provides step-by-step instructions for deploying the Elastic Stack SIEM solution using Docker on an M1 Mac environment. The deployment is designed to be compatible with ARM64 architecture while maintaining cross-platform compatibility for team members using Windows.

## Prerequisites

- M1 Mac with Docker Desktop installed
- At least 4GB of RAM allocated to Docker
- Git (for cloning the repository)
- Basic understanding of Docker and containerization
- Terminal access

## Step 1: Clone the Repository

```bash
git clone https://github.com/Amid68/Elastic-SIEM-Project.git
cd Elastic-SIEM-Project
```

## Step 2: Configure Environment Variables

1. Navigate to the docker directory:
   ```bash
   cd docker
   ```

2. Edit the `.env` file to customize your deployment:
   ```bash
   nano .env
   ```

3. At minimum, change the following variables:
   - `ELASTIC_PASSWORD`: Set a strong password for the Elasticsearch admin user
   - `KIBANA_ENCRYPTION_KEY`: Set a random 32+ character string for Kibana encryption. For this you can use this command:
     
     ```
     openssl rand -base64 32
     ```
   - Adjust memory settings if needed based on your system resources

## Step 3: Deploy the Elastic Stack

1. Start the Elasticsearch container:
   ```bash
   docker-compose up -d elasticsearch
   ```

2. Wait for Elasticsearch to fully initialize (this may take a few minutes):
   ```bash
   docker-compose logs -f elasticsearch
   ```
   
   Wait until you see logs indicating that the service is running properly. Note that a YELLOW status is normal for a single-node cluster.

3. Once Elasticsearch is running, deploy Kibana:
   ```bash
   docker-compose up -d --no-deps kibana
   ```

4. After Kibana is running, deploy Logstash:
   ```bash
   docker-compose up -d --no-deps logstash
   ```

5. Finally, deploy the Beats components:
   ```bash
   docker-compose up -d --no-deps filebeat packetbeat
   ```

   Note: Using the `--no-deps` flag is a workaround for health check issues that may mark Elasticsearch as unhealthy despite it functioning correctly.

## Step 4: Access Kibana

1. Open a web browser and navigate to:
   ```
   http://localhost:5601
   ```

2. Log in with the following credentials:
   - Username: `elastic`
   - Password: The value you set for `ELASTIC_PASSWORD` in the `.env` file

## Step 5: Configure Kibana for SIEM

1. After logging in to Kibana, click on the hamburger menu (☰) in the top-left corner.

2. Navigate to "Security" in the left sidebar.

3. If this is your first time, you'll be prompted to add sample data. You can choose to add it for testing purposes.

4. Configure detection rules:
   - Go to "Security" > "Detections" > "Manage detection rules"
   - Enable the rules relevant to your monitoring needs
   - Create custom rules as needed

5. Set up dashboards:
   - Go to "Security" > "Overview" to see the main SIEM dashboard
   - Explore other dashboards under "Security" > "Explore"

## Step 6: Configure Beats for Data Collection

The Beats agents are already configured with basic settings, but you may need to customize them for your specific environment:

1. Filebeat:
   - Edit `filebeat/filebeat.yml` to add or modify log sources
   - Restart Filebeat after changes: `docker-compose restart filebeat`

2. Packetbeat:
   - Edit `packetbeat/packetbeat.yml` to modify network monitoring settings
   - Restart Packetbeat after changes: `docker-compose restart packetbeat`

## Step 7: Configure Windows Agents (for Windows Team Members)

For Windows team members, Winlogbeat needs to be installed directly on Windows systems:

1. Download Winlogbeat from the [Elastic website](https://www.elastic.co/downloads/beats/winlogbeat)

2. Extract the downloaded package to `C:\Program Files\Winlogbeat`

3. Copy the `winlogbeat/winlogbeat.yml` configuration file to the installation directory

4. Edit the configuration file to point to your Elasticsearch or Logstash instance:
   ```yaml
   output.logstash:
     hosts: ["your-mac-ip-address:5044"]
   ```

5. Install and start the Winlogbeat service:
   ```powershell
   # Run PowerShell as Administrator
   cd 'C:\Program Files\Winlogbeat'
   .\install-service-winlogbeat.ps1
   Start-Service winlogbeat
   ```

## Step 8: Verify Data Collection

1. In Kibana, navigate to "Management" > "Stack Management" > "Index Management"

2. Verify that indices are being created for each Beat:
   - `filebeat-*`
   - `packetbeat-*`
   - `winlogbeat-*` (if Windows agents are configured)

3. Check "Discover" in Kibana to see if data is flowing in

## Step 9: Stopping the Elastic Stack

To stop the Elastic Stack when not in use:

```bash
docker-compose down
```

To stop and remove all data (use with caution):

```bash
docker-compose down -v
```

## Troubleshooting

### Elasticsearch Won't Start

1. Check if you have enough memory allocated to Docker:
   ```bash
   docker info | grep "Total Memory"
   ```

2. Check Elasticsearch logs:
   ```bash
   docker-compose logs elasticsearch
   ```

3. Common issues:
   - Memory limits too low: Increase `ES_JAVA_OPTS` in `.env`
   - Permission issues: Check folder permissions
   - Port conflicts: Ensure ports 9200 and 5601 are not in use

### No Data in Kibana

1. Check if Beats are running:
   ```bash
   docker-compose ps
   ```

2. Check Beats logs:
   ```bash
   docker-compose logs filebeat
   docker-compose logs packetbeat
   ```

3. Verify Logstash is processing data:
   ```bash
   docker-compose logs logstash
   ```

### Environment Variable Issues

If you see errors about undefined environment variables:

1. Check that your `.env` file contains all required variables
2. Verify that the variables are properly referenced in your docker-compose.yml
3. For Logstash specifically, ensure the `ELASTIC_PASSWORD` variable is explicitly defined in the environment section
