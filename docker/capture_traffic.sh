#!/bin/bash

# Directory to store network captures
CAPTURE_DIR="docker/network_logs"
mkdir -p $CAPTURE_DIR

# File names
PCAP_FILE="$CAPTURE_DIR/capture.pcap"
JSON_FILE="$CAPTURE_DIR/network_traffic.json"

# Duration of capture in seconds (adjust as needed)
DURATION=60

echo "Starting network traffic capture for $DURATION seconds..."
echo "Press Ctrl+C to stop early"

# Capture traffic to pcap file
sudo tcpdump -i any -w $PCAP_FILE -G $DURATION -W 1

echo "Converting to JSON format for Elasticsearch..."
# Convert pcap to JSON (requires tshark - part of Wireshark)
tshark -r $PCAP_FILE -T json > $JSON_FILE

echo "Capture complete. Data stored in $JSON_FILE"
echo "This file will be picked up by Filebeat automatically."
